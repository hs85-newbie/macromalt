import pytest


async def _register_and_login(client, email="settings@example.com"):
    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": "설정테스트"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_save_api_key(client):
    token = await _register_and_login(client)
    resp = await client.post(
        "/api/settings/api-keys",
        json={"provider": "openai", "api_key": "sk-test-key-1234567890"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openai"
    assert "is_valid" in data


@pytest.mark.asyncio
async def test_get_api_keys(client):
    token = await _register_and_login(client, "keys@example.com")
    # 먼저 키 저장
    await client.post(
        "/api/settings/api-keys",
        json={"provider": "gemini", "api_key": "test-gemini-key"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        "/api/settings/api-keys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    providers = [item["provider"] for item in data]
    assert "gemini" in providers


@pytest.mark.asyncio
async def test_get_wordpress_settings_not_found(client):
    token = await _register_and_login(client, "wp@example.com")
    resp = await client.get(
        "/api/settings/wordpress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_and_get_wordpress_settings(client):
    token = await _register_and_login(client, "wp2@example.com")
    # 저장
    save_resp = await client.post(
        "/api/settings/wordpress",
        json={
            "site_url": "https://example.com",
            "username": "admin",
            "password": "wp-app-password",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert save_resp.status_code == 200
    data = save_resp.json()
    assert data["site_url"] == "https://example.com"
    assert data["username"] == "admin"

    # 조회
    get_resp = await client.get(
        "/api/settings/wordpress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["site_url"] == "https://example.com"
