
import os
import sys
import shutil
import subprocess
import time
import pytest
import httpx
from pathlib import Path


# Paths for clean server copy
# Copy from project root src/server
SRC = Path(__file__).parent.parent.parent / 'src' / 'mcpo_simple_server'
DST = Path('/tmp/testing/mcpo_simple_server')
CLEAN_URL = 'http://localhost:9999'

# Create test environment directory if it doesn't exist
if not DST.parent.exists():
    DST.mkdir(parents=True, exist_ok=True)

# Add test environment to PYTHONPATH
os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '') + ':/app'
os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '') + ':' + str(DST.parent)


def pytest_addoption(parser):
    parser.addoption(
        '--clean', action='store_true',
        help=f'Start a clean server instance in {DST} on port 9999'
    )
    parser.addoption(
        '--url', action='store',
        default=CLEAN_URL,
        help=f'Override the default server URL. Default: {CLEAN_URL}'
    )


@pytest.fixture(scope='session')
def server_url(request):
    """
    Provide the base URL for tests.

    If --url is specified, use that external server instead of starting a local one.
    If --clean is used, spin up a fresh uvicorn process.
    Otherwise, use an existing server instance if available.
    """
    clean = request.config.getoption('--clean')
    url = request.config.getoption('--url')

    # Check if user provided a custom URL (different from default)
    using_external_server = url != CLEAN_URL

    # If using custom URL, we don't need to start a local server
    if using_external_server:
        print(f"Using external server at {url}")
        # Verify the external server is available
        try:
            r = httpx.get(url + "/api/v1/health", timeout=5)
            if r.status_code == 200:
                print("Connected to external server successfully")
            else:
                pytest.exit(f"External server returned unexpected status: {r.status_code}")
        except Exception as e:
            pytest.exit(f"Could not connect to external server at {url}: {str(e)}")

        # Return the URL without starting a local server
        yield url
        return  # No cleanup needed for external server

    # Local server setup starts here
    # If DST not exists, use it
    if not DST.exists():
        print(f"Creating folder {DST}")
        os.makedirs(DST, exist_ok=True)

    # If clean option is specified, always create a fresh copy
    if clean:
        print(f"Setting up clean test environment in {DST}")
        # Remove existing directory if it exists
        if DST.exists():
            shutil.rmtree(DST)
        # Copy source files to test environment
        shutil.copytree(SRC, DST)
        # Create empty data directory
        shutil.rmtree(DST / 'data', ignore_errors=True)
        os.makedirs(DST / 'data', exist_ok=True)
        # Remove .env file to ensure clean configuration
        (DST / '.env').unlink(missing_ok=True)
    else:
        print(f"Using existing test environment in {DST}")
        # If directory doesn't exist, create it
        if not DST.exists():
            print("Test environment doesn't exist. Creating it now...")
            shutil.copytree(SRC, DST)
            os.makedirs(DST / 'data', exist_ok=True)

    # Prepare environment variables
    env = os.environ.copy()
    env.update({
        'JWT_SECRET_KEY': 'esO9RA/36qmedvGaMwCgHqwu1FiRjVeQiNoXRWpvLZXaCXxXlr1/3hwcKST760tKCg+ZnYI3UhjUiFFdrq/byQ==',
        'API_KEY_ENCRYPTION_KEY': '5zxll-BxzZ3ecE8e1ByvysOorLCuKBJwFssiVW8O8S8='
    })

    # Create log directory if it doesn't exist
    log_dir = Path('/tmp/testing/logs')
    log_dir.mkdir(exist_ok=True, parents=True)

    # Create a single log file with timestamp
    timestamp = int(time.time())
    date = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(timestamp))
    log_file = log_dir / f'server_log_{date}.log'

    print(f"   SERVER-LOG: {log_file}")

    # Start uvicorn server with environment variables and redirect both stdout and stderr to the same log file
    with open(log_file, 'w', encoding='utf-8') as log:
        proc = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'main:app',
            '--host', '0.0.0.0', '--port', '9999', '--reload'
        ], cwd=str(DST), stdout=log, stderr=subprocess.STDOUT, env=env)

    # Wait for server to be ready
    print("Waiting for test server to start...")
    for _ in range(30):
        try:
            r = httpx.get(url + "/api/v1/health", timeout=1)
            if r.status_code == 200:
                print("Test server started successfully")
                break
        except Exception:
            time.sleep(1)
    else:
        proc.terminate()
        pytest.exit("Test server did not start in time")

    yield url

    # Teardown - stop the server but don't remove files if use_existing
    print("Stopping test server...")
    proc.terminate()
    proc.wait(timeout=10)


# Add fixture to obtain and return admin access token for authenticated tests
@pytest.fixture(scope='session')
def admin_auth_token(server_url):       # pylint: disable=redefined-outer-name
    r = httpx.get(f"{server_url}/api/v1/user/me")
    assert r.status_code == 401
    with httpx.Client() as client:
        response = client.post(
            server_url + "/api/v1/user/login", json={"username": "admin", "password": "MCPOadmin"}
        )
    print(response)
    assert response.status_code == 200
    return response.json()["access_token"]
