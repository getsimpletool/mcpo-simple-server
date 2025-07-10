import pytest
import httpx
import json


@pytest.mark.asyncio
async def test_admin_create_and_delete_api_key(server_url, admin_auth_token):
    """
    Test creating and deleting an API key for the current user (admin).
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        resp = await client.post(f"{server_url}/api/v1/user/api-keys", headers=headers)
        assert resp.status_code == 200, f"API key creation failed: {resp.text}"
        api_key = resp.json().get("api_key")
        assert api_key, "No api_key returned in response"
        # Test deleting the API key we just created
        delete_headers = {"Authorization": f"Bearer {admin_auth_token}", "Content-Type": "application/json"}
        delete_resp = await client.request(
            "DELETE",
            f"{server_url}/api/v1/user/api-keys",
            headers=delete_headers,
            content=json.dumps({"api_key": api_key})
        )
        assert delete_resp.status_code == 204, f"API key deletion failed: {delete_resp.text}"
