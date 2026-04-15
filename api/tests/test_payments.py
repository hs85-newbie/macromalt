"""
Toss Payments 라우터 테스트
실제 Toss API 호출은 mock 처리 — Toss 키 없이도 통과
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from models.models import Subscription, User


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
        json={"eventType": "BILLING_SUCCESS", "data": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


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


# ── 9. POST /api/payments/refund (정상) → 환불 완료 ────────────────────────────
@pytest.mark.asyncio
async def test_refund_success(client, async_session):
    token = await _register_and_login(client, "refund_ok@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "refund_ok@example.com")
    )
    user = result.scalar_one()
    user.plan = "pro"

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="bk_refund_ok",
        toss_customer_key=f"macromalt-{user.id}-aaaa1111",
        last_payment_key="pk_refund_ok_12345",
        plan="pro",
        status="active",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"totalAmount": 49900}

    mock_http = AsyncMock()
    mock_http.post.return_value = mock_resp
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("routers.payments.httpx.AsyncClient", return_value=mock_http):
        resp = await client.post(
            "/api/payments/refund",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "환불" in data["message"]
    assert data["refund_amount"] == 49900

    await async_session.refresh(sub)
    assert sub.status == "cancelled"
    assert sub.cancelled_at is not None

    await async_session.refresh(user)
    assert user.plan == "free"


# ── 10. POST /api/payments/refund (구독 없음) → 404 ────────────────────────────
@pytest.mark.asyncio
async def test_refund_no_subscription(client):
    token = await _register_and_login(client, "refund_none@example.com")
    resp = await client.post(
        "/api/payments/refund",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── 11. POST /api/payments/refund (paymentKey 없음) → 400 ──────────────────────
@pytest.mark.asyncio
async def test_refund_no_payment_key(client, async_session):
    token = await _register_and_login(client, "refund_nopk@example.com")

    result = await async_session.execute(
        select(User).where(User.email == "refund_nopk@example.com")
    )
    user = result.scalar_one()

    sub = Subscription(
        user_id=user.id,
        toss_billing_key="bk_nopk",
        toss_customer_key=f"macromalt-{user.id}-bbbb2222",
        last_payment_key=None,
        plan="pro",
        status="active",
        amount=49900,
    )
    async_session.add(sub)
    await async_session.commit()

    resp = await client.post(
        "/api/payments/refund",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
