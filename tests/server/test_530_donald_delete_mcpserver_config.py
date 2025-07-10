import pytest
import httpx
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_530_donald_delete_mcpserver_config(server_url):
    """
    Test deleting an MCP server configuration for non-admin user Donald:
    1. Login as Donald
    2. Add a calculator MCP server
    3. Verify server appears in the list
    4. Delete the server (stops the server and removes its configuration)
    5. Verify server is completely removed from the configuration
    """
    # Donald user credentials
    donald_username = "donald"
    donald_password = "donaldduck"

    async with httpx.AsyncClient() as client:
        # 1. Login as Donald
        login_data = {
            "username": donald_username,
            "password": donald_password
        }

        resp = await client.post(
            f"{server_url}/user/login",
            json=login_data
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        token_data = resp.json()
        assert "access_token" in token_data, f"Expected 'access_token' in response, got {token_data}"

        donald_token = token_data["access_token"]
        donald_headers = {"Authorization": f"Bearer {donald_token}", "Content-Type": "application/json"}

        # 2. Add calculator MCP server
        calculator_server_config = {
            "mcpServers": {
                "calculator": {
                    "command": "uvx",
                    "args": [
                        "mcp-server-calculator"
                    ]
                }
            }
        }

        resp = await client.post(
            f"{server_url}/user/mcpserver",
            headers=donald_headers,
            json=calculator_server_config
        )

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "success", f"Expected 'success', got {data.get('status')}: {data}"
        assert "calculator" in data.get("message", ""), f"Expected server name in message, got {data.get('message')}"

        # 3. Verify server appears in the list
        resp = await client.get(
            f"{server_url}/user/mcpservers",
            headers=donald_headers
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # Find the calculator server in the list
        calculator_server_found = False
        for server in data:
            if server.get("name") == "calculator":
                calculator_server_found = True
                break

        assert calculator_server_found, f"Calculator server not found in server list: {data}"

        # 4. Delete the server (this should stop the server and remove its configuration)
        resp = await client.delete(
            f"{server_url}/user/mcpserver/calculator",
            headers=donald_headers
        )

        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

        # Note: With our changes, the DELETE endpoint now completely removes the server
        # configuration from the user's settings, not just stops the server.

        # 5. Verify server is completely removed from the configuration
        # Check the server list
        resp = await client.get(
            f"{server_url}/user/mcpservers",
            headers=donald_headers
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check if calculator server is in the list
        calculator_server_found = False
        for server in data:
            if server.get("name") == "calculator":
                calculator_server_found = True
                break
        
        assert not calculator_server_found, f"Calculator server still found in server list: {data}"

        logger.info("Successfully verified calculator server was removed from the list")

        # 6. Try to get the specific server configuration to verify it doesn't exist
        resp = await client.get(
            f"{server_url}/user/mcpserver/calculator",
            headers=donald_headers
        )

        # The server should either return 404 Not Found or an empty configuration
        if resp.status_code == 404:
            logger.info("Server returned 404 Not Found for calculator server configuration")
        else:
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            server_config = resp.json()
            logger.info(f"Server configuration response: {server_config}")
            
            # If the server returns a configuration, it should be empty or not contain the calculator server
            if "mcpServers" in server_config:
                assert "calculator" not in server_config["mcpServers"], f"Calculator server still found in configuration: {server_config['mcpServers']}"

        logger.info("Successfully verified calculator server configuration was completely removed")
