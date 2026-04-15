"""
Pipeline 라우터 통합 테스트
실제 파이프라인 실행은 mock 처리 — 외부 연동 없이 통과
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from models.models import PublishedPost, RunLog, User


async def _register_and_login(client, email="pipeline@example.com"):
    """헬퍼: 회원가입 후 access_token 반환"""
    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": "파이프라인테스트"},
    )
    assert reg.status_code == 201
    return reg.json()["access_token"]


# ── 1. POST /api/pipeline/execute (미인증) → 401 ──────────────────────────────
@pytest.mark.asyncio
async def test_execute_pipeline_unauthorized(client):
    resp = await client.post(
        "/api/pipeline/execute",
        json={"slot": "morning"},
    )
    assert resp.status_code == 401


# ── 2. POST /api/pipeline/execute (정상) → 202, run_log_id 반환 ───────────────
@pytest.mark.asyncio
async def test_execute_pipeline_success(client):
    token = await _register_and_login(client, "exec@example.com")
    with patch("routers.pipeline._execute_pipeline_task", new=AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/pipeline/execute",
            json={"slot": "morning"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 202
    data = resp.json()
    assert "run_log_id" in data
    assert "message" in data


# ── 3. POST /api/pipeline/execute (이미 실행 중) → 409 ────────────────────────
@pytest.mark.asyncio
async def test_execute_pipeline_conflict(client, async_session):
    token = await _register_and_login(client, "conflict@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "conflict@example.com")
    )
    user = result.scalar_one()

    run_log = RunLog(
        user_id=user.id,
        status="running",
        slot="morning",
        triggered_by="manual",
        started_at=datetime.now(timezone.utc),
    )
    async_session.add(run_log)
    await async_session.commit()

    with patch("routers.pipeline._execute_pipeline_task", new=AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/pipeline/execute",
            json={"slot": "morning"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 409


# ── 4. GET /api/pipeline/runs (미인증) → 401 ──────────────────────────────────
@pytest.mark.asyncio
async def test_get_run_logs_unauthorized(client):
    resp = await client.get("/api/pipeline/runs")
    assert resp.status_code == 401


# ── 5. GET /api/pipeline/runs (정상) → 200, 목록 반환 ────────────────────────
@pytest.mark.asyncio
async def test_get_run_logs_success(client, async_session):
    token = await _register_and_login(client, "runs@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "runs@example.com")
    )
    user = result.scalar_one()

    run_log = RunLog(
        user_id=user.id,
        status="success",
        slot="morning",
        triggered_by="manual",
        started_at=datetime.now(timezone.utc),
    )
    async_session.add(run_log)
    await async_session.commit()

    resp = await client.get(
        "/api/pipeline/runs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["status"] == "success"


# ── 6. GET /api/pipeline/runs/{run_id} (정상) → 200 ─────────────────────────
@pytest.mark.asyncio
async def test_get_run_log_by_id_success(client, async_session):
    token = await _register_and_login(client, "runid@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "runid@example.com")
    )
    user = result.scalar_one()

    run_log = RunLog(
        user_id=user.id,
        status="success",
        slot="afternoon",
        triggered_by="manual",
        started_at=datetime.now(timezone.utc),
    )
    async_session.add(run_log)
    await async_session.commit()
    await async_session.refresh(run_log)

    resp = await client.get(
        f"/api/pipeline/runs/{run_log.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == run_log.id
    assert data["status"] == "success"


# ── 7. GET /api/pipeline/runs/{run_id} (없는 ID) → 404 ───────────────────────
@pytest.mark.asyncio
async def test_get_run_log_by_id_not_found(client):
    token = await _register_and_login(client, "notfound@example.com")
    resp = await client.get(
        "/api/pipeline/runs/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── 8. GET /api/pipeline/posts (미인증) → 401 ─────────────────────────────────
@pytest.mark.asyncio
async def test_get_published_posts_unauthorized(client):
    resp = await client.get("/api/pipeline/posts")
    assert resp.status_code == 401


# ── 9. GET /api/pipeline/posts (정상) → 200, 목록 반환 ───────────────────────
@pytest.mark.asyncio
async def test_get_published_posts_success(client, async_session):
    token = await _register_and_login(client, "posts@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "posts@example.com")
    )
    user = result.scalar_one()

    post = PublishedPost(
        user_id=user.id,
        title="테스트 포스트",
        category="analysis",
        published_at=datetime.now(timezone.utc),
    )
    async_session.add(post)
    await async_session.commit()

    resp = await client.get(
        "/api/pipeline/posts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "테스트 포스트"
