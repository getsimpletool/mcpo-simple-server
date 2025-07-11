import pytest
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_510_donald_mcpserver_env(server_url, admin_auth_token):
    """
    Comprehensive test of MCP server environment variable management for non-admin user Donald.

    Steps:
    1. Ensure Donald user is created and logged in
    2. Add a 'calculator' MCP server for Donald
    3. Set environment variables on the server
    4. Verify environment variables via server config
    5. Update a single environment variable
    6. Execute the 'calculate' tool to verify environment effect
    7. Verify environment update via server config
    8. Delete a single environment variable and verify
    9. Delete all environment variables and verify
    10. Clean up by stopping the MCP server
    """
    # Donald user credentials
    donald_username = "donald"
    donald_password = "donaldduck"

    async with httpx.AsyncClient() as client:
        admin_headers = {"Authorization": f"Bearer {admin_auth_token}", "Content-Type": "application/json"}

        # Step 1: Ensure Donald user is created and logged in
        resp = await client.delete(
            f"{server_url}/api/v1/admin/user/{donald_username}",
            headers=admin_headers
        )
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
        donald_headers = {"Authorization": f"Bearer {donald_token}", "Content-Type": "application/json"}

        # Step 2: Add a 'calculator' MCP server for Donald
        try:
            resp = await client.delete(
                f"{server_url}/api/v1/mcpservers/calculator",
                headers=donald_headers
            )
            logger.info("Cleanup: Deleted existing calculator server, status: %s", resp.status_code)
        except Exception as e:
            logger.warning("Cleanup: Failed to delete calculator server: %s", str(e))

        calculator_server_config = {
            "mcpServers": {
                "calculator": {
                    "command": "uvx",
                    "args": ["mcp-server-calculator"]
                }
            }
        }
        resp = await client.post(
            f"{server_url}/api/v1/mcpservers",
            headers=donald_headers,
            json=calculator_server_config
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected a list, got {type(data)}: {data}"
        assert len(data) > 0, f"Expected non-empty list, got {data}"
        server = data[0]
        assert server.get("status") in ("running", "configured"), f"Expected 'running' or 'configured', got {server.get('status')}: {server}"

        # Wait a bit for the server to initialize
        await asyncio.sleep(2)

        # Step 3: Set environment variables on the server
        env_data = {
            "env": {
                "CALCULATOR_MODE": "scientific",
                "CALCULATOR_PRECISION": "10"
            }
        }
        resp = await client.put(
            f"{server_url}/api/v1/mcpservers/calculator/env",
            headers=donald_headers,
            json=env_data
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

        # Step 4: Verify environment variables via server config
        resp = await client.get(
            f"{server_url}/api/v1/mcpservers/calculator/config",
            headers=donald_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        user_data = resp.json()
        assert "env" in user_data, f"Expected 'env' in response, got {user_data}"
        env_data = user_data["env"]
        assert env_data.get("CALCULATOR_MODE") == "scientific", f"Expected 'scientific', got {env_data.get('CALCULATOR_MODE')}"
        assert env_data.get("CALCULATOR_PRECISION") == "10", f"Expected '10', got {env_data.get('CALCULATOR_PRECISION')}"

        # Step 5: Update a single environment variable
        resp = await client.put(
            f"{server_url}/api/v1/mcpservers/calculator/env/CALCULATOR_MODE",
            headers=donald_headers,
            json={"value": "basic"}
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

        # Step 6: Execute the 'calculate' tool to verify environment effect
        tool_args = {"expression": "2+3"}
        resp = await client.post(
            f"{server_url}/api/v1/user/tool/calculator/calculate",
            headers=donald_headers,
            json=tool_args
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        tool_result = resp.json()
        assert tool_result[0] == 5, f"Expected result 5, got {tool_result[0]}"

        # Step 7: Verify environment update via server config
        resp = await client.get(
            f"{server_url}/api/v1/mcpservers/calculator/config",
            headers=donald_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        user_data = resp.json()
        assert "env" in user_data, f"Expected 'env' in response, got {user_data}"
        env_data = user_data["env"]
        assert env_data.get("CALCULATOR_MODE") == "basic", f"Expected 'basic', got {env_data.get('CALCULATOR_MODE')}"
        assert env_data.get("CALCULATOR_PRECISION") == "10", f"Expected '10', got {env_data.get('CALCULATOR_PRECISION')}"

        # Step 8: Delete a single environment variable and verify
        resp = await client.delete(
            f"{server_url}/api/v1/mcpservers/calculator/env/CALCULATOR_MODE",
            headers=donald_headers
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"
        resp = await client.get(
            f"{server_url}/api/v1/mcpservers/calculator/config",
            headers=donald_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        user_data = resp.json()
        assert "env" in user_data, f"Expected 'env' in response, got {user_data}"
        env_data = user_data["env"]
        assert "CALCULATOR_MODE" not in env_data, f"Expected 'CALCULATOR_MODE' to be deleted, got {env_data}"
        assert env_data.get("CALCULATOR_PRECISION") == "10", f"Expected '10', got {env_data.get('CALCULATOR_PRECISION')}"

        # Step 9: Delete all environment variables and verify
        resp = await client.delete(
            f"{server_url}/api/v1/mcpservers/calculator/env",
            headers=donald_headers
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"
        resp = await client.get(
            f"{server_url}/api/v1/mcpservers/calculator/config",
            headers=donald_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        user_data = resp.json()
        assert "env" in user_data, f"Expected 'env' in response, got {user_data}"
        assert user_data["env"] == {}, f"Expected empty env dict, got {user_data['env']}"

        # Step 10: Clean up by stopping the MCP server
        resp = await client.delete(
            f"{server_url}/api/v1/mcpservers/calculator",
            headers=donald_headers
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"
        print("Successfully tested environment variables for calculator server for user: " + donald_username)
