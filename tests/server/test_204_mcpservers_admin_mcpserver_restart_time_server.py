"""Test for MCP server restart functionality."""
import json

import httpx
import pytest


@pytest.mark.asyncio
async def test_admin_mcpserver_restart(server_url, admin_auth_token):
    """
    Test the full lifecycle of a MCP server with restart:
    1. Create and start a new time server
    2. Verify it's running
    3. Stop the server
    4. Verify it's stopped
    5. Start it again
    6. Verify it's running
    7. Delete the server
    8. Verify it's deleted
    """
    headers = {"Authorization": f"Bearer {admin_auth_token}", "Content-Type": "application/json"}
    server_name = "test_restart_server"

    # Clean up existing test server if it exists
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"{server_url}/api/v1/mcpservers/{server_name}",
            headers=headers
        )
    # 1. Create and start a new time server
    time_server_config = {
        "mcpServers": {
            server_name: {
                "command": "uvx",
                "args": [
                    "mcp-server-time",
                    "--local-timezone=Europe/Warsaw"
                ],
                "env": {},
                "description": "Test restart server",
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
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

        # 2. Verify server is running
        resp = await client.get(f"{server_url}/api/v1/mcpservers/{server_name}/status", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        server_status = resp.json()
        assert server_status.get("status") == "running", f"Expected 'running', got {server_status.get('status')}"

        # 3. Stop the server
        resp = await client.post(
            f"{server_url}/api/v1/mcpservers/{server_name}/stop",
            headers=headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        # 4. Verify server is stopped
        resp = await client.get(f"{server_url}/api/v1/mcpservers/{server_name}/status", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        server_status = resp.json()
        assert server_status.get("status") == "stopped", f"Expected 'stopped', got {server_status.get('status')}"

        # 5. Start the server again
        resp = await client.post(
            f"{server_url}/api/v1/mcpservers/{server_name}/start",
            headers=headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        # 6. Verify server is running again
        resp = await client.get(f"{server_url}/api/v1/mcpservers/{server_name}/status", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        server_status = resp.json()
        assert server_status.get("status") == "running", f"Expected 'running', got {server_status.get('status')}"

        # 7. Delete the server
        resp = await client.delete(f"{server_url}/api/v1/mcpservers/{server_name}", headers=headers)
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"

        # 8. Verify server is deleted
        resp = await client.get(f"{server_url}/api/v1/mcpservers/{server_name}/status", headers=headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
