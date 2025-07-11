import pytest
import httpx
import json
import asyncio


@pytest.mark.asyncio
async def test_admin_mcpserver_lifecycle(server_url, admin_auth_token):
    """
    Test the full lifecycle of a MCP server:
    1. Create a new server via POST /api/v1/mcpserver
    2. Verify it appears in GET /api/v1/mcpservers
    3. Use a tool from the server via /tool/time/get_current_time
    """
    headers = {"Authorization": f"Bearer {admin_auth_token}", "Content-Type": "application/json"}

    # Clean up existing time servers with admin
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{server_url}/api/v1/mcpservers/time", headers=headers)
        # Just check response.. do not veryfie it
        print(resp)

    # 1. Create a new "time" server with specified configuration
    time_server_config = {
        "mcpServers": {
            "time": {
                "command": "uvx",
                "args": [
                    "mcp-server-time",
                    "--local-timezone=Europe/Warsaw"
                ],
                "env": {},
                "description": "time server",
                "disabled": False
            }
        }
    }

    async with httpx.AsyncClient() as client:
        # Add the server
        resp = await client.post(
            f"{server_url}/api/v1/mcpservers",
            headers=headers,
            content=json.dumps(time_server_config)
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected a list, got {type(data)}: {data}"
        assert len(data) > 0, f"Expected non-empty list, got {data}"
        server = data[0]
        assert server.get("status") in ("success", "running"), f"Expected 'success' or 'running', got {server.get('status')}: {server}"

        # 2. Verify server appears in the list
        resp = await client.get(f"{server_url}/api/v1/mcpservers/config", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "mcpServers" in data, f"Expected 'mcpServers' key in response, got {data}"

        # Find the time server in the list
        time_server_found = False
        for server_name, _ in data["mcpServers"].items():
            if server_name == "time":
                time_server_found = True
                break

        assert time_server_found, f"Time server not found in server list: {data['mcpServers']}"

        # 3. Wait a bit for the server to initialize and tools to be available
        await asyncio.sleep(2)

        # 4. Use a tool from the server - provide the required timezone parameter
        resp = await client.post(
            f"{server_url}/api/v1/user/tool/time/get_current_time",
            headers=headers,
            json={"timezone": "Europe/Warsaw"}
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()

        # The response is a list containing the time data
        assert isinstance(data, list), f"Expected a list in response, got {data}"
        assert len(data) > 0, f"Expected non-empty list, got {data}"

        # Extract the actual time data from the first element of the list
        time_data = data[0]

        # Verify the timezone is correct
        assert "timezone" in time_data, f"Expected 'timezone' in time data, got {time_data}"
        assert time_data["timezone"] == "Europe/Warsaw", f"Expected timezone 'Europe/Warsaw', got {time_data['timezone']}"

        # Verify datetime is present
        assert "datetime" in time_data, f"Expected 'datetime' in time data, got {time_data}"

        # 5. CLeanup - remove the server
        resp = await client.delete(f"{server_url}/api/v1/mcpservers/time", headers=headers)
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"
