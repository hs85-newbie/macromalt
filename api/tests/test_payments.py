"""
Toss Payments 라우터 테스트
실제 Toss API 호출은 mock 처리 — Toss 키 없이도 통과
"""
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from core.config import settings
from models.models import Subscription, User


def _toss_webhook_auth() -> str:
    """웹훅 테스트용 Toss Authorization 헤더 (서명 검증 통과)"""
    credentials = base64.b64encode(f"{settings.TOSS_SECRET_KEY}:".encode()).decode()
    return f"Basic {credentials}"


async def _register_and_login(client, email="pay@example.com"):
    """헬퍼: 회원가입 후 access_token 반환"""
    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": "결제테스트"},
    )
    assert reg.status_code == 201
    return reg.json()["access_token"]


# ── 1. GET /api/payments/subscription (구독 없음) → plan=free ──────────────────
@pytest.mark.asyncio
async def test_get_subscription_no_sub(client):
    token = await _register_and_login(client, "sub_none@example.com")
    resp = await client.get(
        "/api/payments/subscription",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert data["amount"] == 0
    assert data["next_billing_at"] is None


# ── 2. POST /api/payments/ready → checkout_url, customer_key 존재 ──────────────
@pytest.mark.asyncio
async def test_payment_ready(client):
    token = await _register_and_login(client, "ready@example.com")
    resp = await client.post(
        "/api/payments/ready",
        json={"plan": "pro", "amount": 49900},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "checkout_url" in data
    assert "customer_key" in data
    assert "order_id" in data
    assert "billing.tosspayments.com" in data["checkout_url"]
    assert "macromalt-" in data["customer_key"]


# ── 3. POST /api/payments/ready (인증 없음) → 401 ──────────────────────────────
@pytest.mark.asyncio
async def test_payment_ready_unauthorized(client):
    resp = await client.post(
        "/api/payments/ready",
        json={"plan": "pro", "amount": 49900},
    )
    assert resp.status_code == 401


# ── 4. POST /api/payments/subscription/cancel (구독 없음) → 404 ────────────────
@pytest.mark.asyncio
async def test_cancel_subscription_no_sub(client):
    token = await _register_and_login(client, "cancel_none@example.com")
    resp = await client.post(
        "/api/payments/subscription/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── 5. POST /api/payments/webhook (BILLING_SUCCESS) → 200 ok ──────────────────
@pytest.mark.asyncio
async def test_webhook_billing_success(client, async_session):
    # 먼저 유저와 구독 레코드를 직접 DB에 삽입
    token = await _register_and_login(client, "webhook@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "webhook@example.com")
    )
    user = result.scalar_one()

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="test_billing_key_abc",
        toss_customer_key=f"macromalt-{user.id}-deadbeef",
        plan="pro",
        status="inactive",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    resp = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": _toss_webhook_auth()},
        json={
            "eventType": "BILLING_SUCCESS",
            "data": {"billingKey": "test_billing_key_abc"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    await async_session.refresh(sub)
    assert sub.status == "active"
    assert sub.next_billing_at is not None

    await async_session.refresh(user)
    assert user.plan == "pro"


# ── 6. POST /api/payments/webhook (BILLING_FAILED) → plan=free ────────────────
@pytest.mark.asyncio
async def test_webhook_billing_failed(client, async_session):
    token = await _register_and_login(client, "failed@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "failed@example.com")
    )
    user = result.scalar_one()
    user.plan = "pro"

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="test_billing_key_fail",
        toss_customer_key=f"macromalt-{user.id}-cafebabe",
        plan="pro",
        status="active",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    resp = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": _toss_webhook_auth()},
        json={
            "eventType": "BILLING_FAILED",
            "data": {"billingKey": "test_billing_key_fail"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    await async_session.refresh(sub)
    assert sub.status == "inactive"

    await async_session.refresh(user)
    assert user.plan == "free"


# ── 7. POST /api/payments/webhook (빌링키 없음) → 200 ok (무시) ────────────────
@pytest.mark.asyncio
async def test_webhook_no_billing_key(client):
    resp = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": _toss_webhook_auth()},
        json={"eventType": "BILLING_SUCCESS", "data": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── 9. POST /api/payments/webhook (서명 검증 실패) → 401 ──────────────────────
@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    resp = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": "Basic invalid_signature"},
        json={"eventType": "BILLING_SUCCESS", "data": {}},
    )
    assert resp.status_code == 401


# ── 10. POST /api/payments/webhook (재현공격 방지) → 두 번째는 무시 ─────────────
@pytest.mark.asyncio
async def test_webhook_replay_attack_prevention(client, async_session):
    from routers.payments import _webhook_id_cache

    payment_key = "unique_test_payment_key_replay_9999"
    # 혹시 이전 테스트에서 남은 캐시 항목 제거
    _webhook_id_cache.pop(payment_key, None)

    token = await _register_and_login(client, "replay@example.com")
    result = await async_session.execute(
        select(User).where(User.email == "replay@example.com")
    )
    user = result.scalar_one()

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="test_billing_key_replay",
        toss_customer_key=f"macromalt-{user.id}-replay001",
        plan="pro",
        status="inactive",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    payload = {
        "eventType": "BILLING_SUCCESS",
        "data": {"billingKey": "test_billing_key_replay", "paymentKey": payment_key},
    }

    # 첫 번째 요청: 정상 처리
    resp1 = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": _toss_webhook_auth()},
        json=payload,
    )
    assert resp1.status_code == 200

    await async_session.refresh(sub)
    assert sub.status == "active"

    # 두 번째 요청 (동일 paymentKey): 재현공격 — 무시
    sub.status = "inactive"
    await async_session.commit()

    resp2 = await client.post(
        "/api/payments/webhook",
        headers={"Authorization": _toss_webhook_auth()},
        json=payload,
    )
    assert resp2.status_code == 200

    # 두 번째 요청은 무시되어 DB 상태 변경 없음
    await async_session.refresh(sub)
    assert sub.status == "inactive"


# ── 8. POST /api/payments/subscription/cancel (활성 구독) → 해지 성공 ───────────
@pytest.mark.asyncio
async def test_cancel_subscription_active(client, async_session):
    token = await _register_and_login(client, "cancel_active@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "cancel_active@example.com")
    )
    user = result.scalar_one()
    user.plan = "pro"

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="test_billing_key_cancel",
        toss_customer_key=f"macromalt-{user.id}-12345678",
        plan="pro",
        status="active",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    resp = await client.post(
        "/api/payments/subscription/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "해지" in resp.json()["message"]

    await async_session.refresh(sub)
    assert sub.status == "cancelled"
    assert sub.cancelled_at is not None

    await async_session.refresh(user)
    assert user.plan == "free"
