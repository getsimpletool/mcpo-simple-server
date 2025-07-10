import pytest
import httpx


@pytest.mark.asyncio
async def test_root_page(server_url):
    r = await httpx.AsyncClient().get(f"{server_url}/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_api_health(server_url):
    r = await httpx.AsyncClient().get(f"{server_url}/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "uptime" in data
    assert isinstance(data["uptime"], str)


@pytest.mark.asyncio
async def test_api_ping(server_url):
    r = await httpx.AsyncClient().get(f"{server_url}/api/v1/ping")
    assert r.status_code == 200
    assert r.json() == {"response": "pong"}


@pytest.mark.asyncio
async def test_api_user_me_unauth(server_url):
    r = await httpx.AsyncClient().get(f"{server_url}/api/v1/user/me")
    assert r.status_code == 401
    assert r.json() == {"detail": "Not authenticated"}
