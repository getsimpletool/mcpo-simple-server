import pytest
import httpx


@pytest.mark.asyncio
async def test_admin_user_env_crud(server_url, admin_auth_token):
    """
    Test full CRUD cycle for user environment variables:
    - PUT /api/v1/user/env (set env)
    - GET /api/v1/user/env (read env)
    - PUT /api/v1/user/env/{key} (update single key)
    - DELETE /api/v1/user/env/{key} (delete single key)
    - DELETE /api/v1/user/env (delete all env)
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {admin_auth_token}"}

        # 1. PUT /api/v1/user/env - set initial env
        # Send env data in the format expected by the API
        env_data = {"env": {"FOO": "bar", "BAZ": "qux"}}
        resp = await client.put(f"{server_url}/api/v1/user/env", headers=headers, json=env_data)
        assert resp.status_code == 204

        # 2. GET /api/v1/user/env - read back
        resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert resp.status_code == 200

        # 3. PUT /api/v1/user/env/FOO - update single key
        resp = await client.put(f"{server_url}/api/v1/user/env/FOO", headers=headers, json={"value": "newbar"})
        assert resp.status_code == 204

        # 4. DELETE /api/v1/user/env/FOO - delete single key
        resp = await client.delete(f"{server_url}/api/v1/user/env/FOO", headers=headers)
        assert resp.status_code == 204

        # 5. DELETE /api/v1/user/env - delete all
        resp = await client.delete(f"{server_url}/api/v1/user/env", headers=headers)
        assert resp.status_code == 204, f"Failed to delete all env: {resp.text}"
        resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert resp.status_code == 200
