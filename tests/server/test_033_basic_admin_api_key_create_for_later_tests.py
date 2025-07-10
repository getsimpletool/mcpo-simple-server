import pytest
import httpx


@pytest.mark.asyncio
async def test_admin_create_api_key_for_later_tests(server_url, admin_auth_token):
    """
    Create an API key for the current user (admin) that will be used in later tests.
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {admin_auth_token}"}
        resp = await client.post(f"{server_url}/api/v1/user/api-keys", headers=headers)
        assert resp.status_code == 200, f"API key creation failed: {resp.text}"
        api_key = resp.json().get("api_key")
        assert api_key, "No api_key returne/mnt/github/getsimpletool/mcpo-simple-server/tests/server/test_108_admin_api_key_create_for_later_tests.pyd in response"

        # Store the API key for later tests
        with open("/tmp/testing/test_api_key.txt", "w", encoding="utf-8") as f:
            f.write(api_key)
