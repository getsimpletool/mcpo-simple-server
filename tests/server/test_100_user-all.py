import pytest
import httpx
import asyncio


@pytest.mark.asyncio
async def test_admin_user_login(server_url):
    """Test user login endpoint to get access token."""
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        assert "token_type" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_user_me(server_url):
    """Test user/me endpoint with and without authentication."""
    async with httpx.AsyncClient() as client:
        # First test without authentication
        resp = await client.get(f"{server_url}/api/v1/user/me")
        assert resp.status_code == 401
        assert resp.json() == {"detail": "Not authenticated"}

        # Now test with authentication
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await client.get(f"{server_url}/api/v1/user/me", headers=headers)
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["username"] == "admin"
        assert "group" in data
        assert data["group"] == "admins"


@pytest.mark.asyncio
async def test_admin_update_password(server_url):
    """Test password update and rollback as requested."""
    async with httpx.AsyncClient() as client:
        # Login to get token
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Change password to MCPadmin123
        resp = await client.put(
            f"{server_url}/api/v1/user/password",
            headers=headers,
            json={"current_password": "MCPOadmin", "new_password": "MCPadmin123"}
        )
        assert resp.status_code == 204

        # Verify login with new credentials
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPadmin123"}
        )
        assert login_resp.status_code == 200
        new_token = login_resp.json().get("access_token")
        assert new_token is not None

        # Add a small delay to ensure password update is processed
        await asyncio.sleep(1)

        # Change password back to MCPOadmin
        rollback_resp = await client.put(
            f"{server_url}/api/v1/user/password",
            headers={"Authorization": f"Bearer {new_token}"},
            json={"current_password": "MCPadmin123", "new_password": "MCPOadmin"}
        )
        assert rollback_resp.status_code == 204

        # Verify login with original credentials
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_user_config(server_url):
    """Test getting user configuration."""
    async with httpx.AsyncClient() as client:
        # Login to get token
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get user config
        resp = await client.get(f"{server_url}/api/v1/user/config", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_admin_api_keys(server_url):
    """Test API key creation and deletion."""
    async with httpx.AsyncClient() as client:
        # Login to get token
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Create API key
        create_resp = await client.post(
            f"{server_url}/api/v1/user/api-keys",
            headers=headers,
            json={"name": "test-key", "expires_in": 3600}
        )
        assert create_resp.status_code == 200
        key_data = create_resp.json()
        assert "api_key" in key_data
        # The API doesn't return key_id directly, it's part of the API key
        api_key = key_data["api_key"]

        # Delete the API key - server expects the full API key in the request body
        # For DELETE requests with a body, we need to use the httpx.AsyncClient.request method
        delete_resp = await client.request(
            "DELETE",
            f"{server_url}/api/v1/user/api-keys",
            headers=headers,
            json={"api_key": api_key}
        )
        assert delete_resp.status_code in [200, 202, 204]  # Accept any success code


@pytest.mark.asyncio
async def test_admin_user_env(server_url):
    """Test user environment variables operations."""
    async with httpx.AsyncClient() as client:
        # Login to get token
        login_resp = await client.post(
            f"{server_url}/api/v1/user/login",
            json={"username": "admin", "password": "MCPOadmin"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get user env (may be empty initially)
        get_resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert get_resp.status_code == 200

        # Try updating a single env variable first
        single_update_resp = await client.put(
            f"{server_url}/api/v1/user/env/TEST_KEY",
            headers=headers,
            json={"value": "test_value"}
        )
        assert single_update_resp.status_code in [200, 201, 204]  # Accept any success code

        # Verify env was updated
        get_resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert get_resp.status_code == 200
        env_data = get_resp.json()
        assert "TEST_KEY" in env_data
        assert env_data["TEST_KEY"] == "test_value"

        # Update specific env key
        key_update_resp = await client.put(
            f"{server_url}/api/v1/user/env/TEST_KEY",
            headers=headers,
            json={"value": "updated_value"}
        )
        assert key_update_resp.status_code in [200, 204]  # Accept either success code

        # Verify specific key was updated
        get_resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert get_resp.status_code == 200
        env_data = get_resp.json()
        assert env_data["TEST_KEY"] == "updated_value"

        # Delete specific env key
        delete_key_resp = await client.delete(
            f"{server_url}/api/v1/user/env/TEST_KEY",
            headers=headers
        )
        assert delete_key_resp.status_code == 204

        # Verify key was deleted
        get_resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert get_resp.status_code == 200
        env_data = get_resp.json()
        assert "TEST_KEY" not in env_data

        # Delete all env variables
        delete_all_resp = await client.delete(
            f"{server_url}/api/v1/user/env",
            headers=headers
        )
        assert delete_all_resp.status_code == 204

        # Verify all env variables were deleted
        get_resp = await client.get(f"{server_url}/api/v1/user/env", headers=headers)
        assert get_resp.status_code == 200
        env_data = get_resp.json()
        assert isinstance(env_data, dict)
        assert len(env_data) == 0
