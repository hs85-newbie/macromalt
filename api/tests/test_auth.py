import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123", "name": "테스트"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123", "name": "중복"}
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "password123", "name": "로그인"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={"email": "wrong@example.com", "password": "password123", "name": "오류"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client):
    reg = await client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "password123", "name": "나"},
    )
    token = reg.json()["access_token"]
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_without_token(client):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client):
    """refresh 후 구 토큰은 재사용 불가 (블랙리스트)."""
    reg = await client.post(
        "/api/auth/register",
        json={"email": "rotate@example.com", "password": "password123", "name": "회전"},
    )
    old_refresh = reg.json()["refresh_token"]

    # 첫 번째 refresh — 성공
    resp = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200

    # 구 토큰 재사용 — 블랙리스트로 인해 실패
    resp2 = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_logout_blacklists_token(client):
    """logout 후 refresh_token은 사용 불가."""
    reg = await client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "password123", "name": "로그아웃"},
    )
    refresh_token = reg.json()["refresh_token"]

    # logout
    resp = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204

    # 로그아웃된 토큰으로 refresh 시도 — 실패
    resp2 = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_logout_idempotent(client):
    """logout은 멱등 — 같은 토큰으로 두 번 호출해도 오류 없음."""
    reg = await client.post(
        "/api/auth/register",
        json={"email": "idem@example.com", "password": "password123", "name": "멱등"},
    )
    refresh_token = reg.json()["refresh_token"]

    await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    resp = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204
