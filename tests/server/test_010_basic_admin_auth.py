import pytest
import httpx

# First logn will create account file for admin


@pytest.mark.asyncio
async def test_admin_login(server_url):
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login", json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        assert token is not None, "No access_token received"

        # Use token for authenticated request
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await client.get(f"{server_url}/api/v1/user/me", headers=headers)
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["username"] == "admin"
