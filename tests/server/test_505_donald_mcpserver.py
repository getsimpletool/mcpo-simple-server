import asyncio
import httpx
import pytest


@pytest.mark.asyncio
async def test_505_donald_mcpserver(server_url, admin_auth_token):
    """
    Test MCP server functionality for non-admin user Donald:
    1. Login as Donald
    2. Add two private MCP servers
    3. List private MCP servers
    4. Verify both servers are visible
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
        donald_headers = {"Authorization": f"Bearer {donald_token}", "Content-Type": "application/json"}

        # 2. Add first MCP server (time server)
        time_server_config = {
            "mcpServers": {
                "time": {
                    "command": "uvx",
                    "args": [
                        "mcp-server-time",
                        "--local-timezone=Europe/Warsaw"
                    ]
                }
            }
        }

        resp = await client.post(
            f"{server_url}/api/v1/mcpservers",
            headers=donald_headers,
            json=time_server_config
        )

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "running", f"Expected 'running', got {data.get('status')}: {data}"

        # Wait a bit for the server to initialize
        await asyncio.sleep(2)

        # 3. Add second MCP server (calculator server)
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
            f"{server_url}/api/v1/mcpservers",
            headers=donald_headers,
            json=calculator_server_config
        )

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "running", f"Expected 'running', got {data.get('status')}: {data}"

        # Wait a bit for the server to initialize
        await asyncio.sleep(2)

        # 4. List private MCP servers
        resp = await client.get(
            f"{server_url}/api/v1/mcpservers/config",
            headers=donald_headers
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        servers = resp.json().get("mcpServers")
        print(servers)

        # Verify both servers are in the list
        server_names = [server_name for server_name, server in servers.items()]
        assert "time" in server_names, f"Expected 'time' in server list, got {server_names}"
        assert "calculator" in server_names, f"Expected 'calculator' in server list, got {server_names}"

        # 5. Verify server details
        for server_name, server in servers.items():
            if server.get("name") == "time":
                assert server.get("status") == "running", f"Expected status 'running', got {server.get('status')}"
            elif server.get("name") == "calculator":
                assert server.get("status") == "running", f"Expected status 'running', got {server.get('status')}"

        print(f"Successfully created and verified two private MCP servers for user: {donald_username}")

        # 6. Clean up - stop the servers
        for server_name in ["time", "calculator"]:
            resp = await client.delete(
                f"{server_url}/api/v1/mcpservers/{server_name}",
                headers=donald_headers
            )
            assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"
            print(f"Successfully stopped server: {server_name}")
