import pytest
import httpx
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_507_donald_create_api_key(server_url, admin_auth_token):
    """
    Test creating an API key for the non-admin user Donald.
    The API key will be saved for use in subsequent tests.
    """
    # Donald user credentials
    donald_username = "donald"
    donald_password = "donaldduck"

    async with httpx.AsyncClient() as client:
        admin_headers = {"Authorization": f"Bearer {admin_auth_token}", "Content-Type": "application/json"}

        # Pre req: delete if donald exists
        resp = await client.delete(
            f"{server_url}/api/v1/admin/user/{donald_username}",
            headers=admin_headers
        )
        # Create donald user
        user_data = {
            "username": donald_username,
            "password": donald_password,
            "group": "users",
            "disabled": False
        }
        resp = await client.post(
            f"{server_url}/api/v1/admin/user",
            headers=admin_headers,
            json=user_data
        )

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

        # 1. Login as Donald
        login_data = {
            "username": donald_username,
            "password": donald_password
        }

        resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json=login_data
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        token_data = resp.json()
        assert "access_token" in token_data, f"Expected 'access_token' in response, got {token_data}"

        donald_token = token_data["access_token"]
        donald_headers = {"Authorization": f"Bearer {donald_token}"}

        # 2. Create API key for Donald
        resp = await client.post(
            f"{server_url}/api/v1/user/api-keys",
            headers=donald_headers
        )

        assert resp.status_code == 200, f"API key creation failed: {resp.text}"
        api_key_response = resp.json()
        assert "api_key" in api_key_response, f"No api_key returned in response: {api_key_response}"

        api_key = api_key_response.get("api_key")
        logger.info("Created API key for Donald: %s...", api_key[:5])

        # Store for next tests
        with open("/tmp/donald_api_key.txt", "w", encoding="utf-8") as f:
            f.write(api_key)
