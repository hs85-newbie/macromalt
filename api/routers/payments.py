import base64
import logging
import uuid
import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = logging.getLogger("macromalt")
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.models import Subscription, User
from schemas.schemas import (
    PaymentReadyRequest,
    PaymentReadyResponse,
    RefundResponse,
    SubscriptionResponse,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])

TOSS_BASE = "https://api.tosspayments.com/v1"


def _toss_auth_header() -> str:
    credentials = base64.b64encode(f"{settings.TOSS_SECRET_KEY}:".encode()).decode()
    return f"Basic {credentials}"


# ── 1. 결제 준비 ──────────────────────────────────────────────
@router.post("/ready", response_model=PaymentReadyResponse)
async def payment_ready(
    body: PaymentReadyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer_key = f"macromalt-{current_user.id}-{secrets.token_hex(8)}"
    order_id = f"order-{uuid.uuid4().hex[:16]}"

    success_url = f"{settings.RAILWAY_URL}/api/payments/confirm"
    fail_url = f"{settings.RAILWAY_URL}/api/payments/fail"

    checkout_url = (
        f"https://billing.tosspayments.com/auth/iss/3.0"
        f"?clientKey={settings.TOSS_CLIENT_KEY}"
        f"&customerKey={customer_key}"
        f"&successUrl={success_url}"
        f"&failUrl={fail_url}"
    )

    return PaymentReadyResponse(
        checkout_url=checkout_url,
        customer_key=customer_key,
        order_id=order_id,
    )


# ── 2. 빌링키 발급 확인 (Toss 리다이렉트 콜백) ─────────────────
@router.post("/confirm")
async def payment_confirm(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    auth_key = body.get("authKey")
    customer_key = body.get("customerKey")

    if not auth_key or not customer_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="authKey, customerKey 필요",
        )

    auth_header = _toss_auth_header()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TOSS_BASE}/billing/authorizations/issue",
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json",
            },
            json={"authKey": auth_key, "customerKey": customer_key},
        )

    if resp.status_code != 200:
        logger.error(f"[Toss] 빌링키 발급 실패 (HTTP {resp.status_code}): {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빌링키 발급 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )

    data = resp.json()
    billing_key = data["billingKey"]

    # customerKey 형식: macromalt-{user_id}-{token}
    try:
        user_id = int(customer_key.split("-")[1])
    except (IndexError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customerKey 형식 오류",
        )

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 없음",
        )

    # 즉시 첫 결제 실행
    order_id = f"order-{uuid.uuid4().hex[:16]}"
    async with httpx.AsyncClient() as client:
        charge_resp = await client.post(
            f"{TOSS_BASE}/billing/{billing_key}",
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json",
            },
            json={
                "customerKey": customer_key,
                "amount": 49900,
                "orderId": order_id,
                "orderName": "macromalt Pro 구독",
                "customerEmail": user.email,
            },
        )

    if charge_resp.status_code != 200:
        logger.error(f"[Toss] 결제 실패 (HTTP {charge_resp.status_code}): {charge_resp.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="결제 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )

    charge_data = charge_resp.json()
    sub = Subscription(
        user_id=user_id,
        toss_billing_key=billing_key,
        toss_customer_key=customer_key,
        last_payment_key=charge_data.get("paymentKey"),
        plan="pro",
        status="active",
        amount=49900,
        next_billing_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(sub)
    user.plan = "pro"
    await db.commit()

    return {"message": "구독 활성화 완료", "plan": "pro"}


# ── 3. Toss 웹훅 수신 ─────────────────────────────────────────
@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    # Toss 2024-06-01 API: eventType 필드로 구분
    event_type = body.get("eventType", "")
    data = body.get("data", {})

    # 빌링키는 data.billingKey 또는 data.payment.billingKey 경로 모두 허용
    billing_key = data.get("billingKey") or data.get("payment", {}).get("billingKey")
    payment_status = data.get("status", "")  # DONE / CANCELED / ABORTED 등

    sub = None
    if billing_key:
        result = await db.execute(
            select(Subscription).where(Subscription.toss_billing_key == billing_key)
        )
        sub = result.scalar_one_or_none()

    # billingKey 없거나 못 찾은 경우: customerKey 또는 customerEmail로 fallback 조회
    if not sub:
        customer_key = data.get("customerKey")
        customer_email = data.get("customerEmail")
        if customer_key:
            result = await db.execute(
                select(Subscription).where(Subscription.toss_customer_key == customer_key)
                .order_by(Subscription.created_at.desc())
            )
            sub = result.scalar_one_or_none()
        if not sub and customer_email:
            user_result = await db.execute(
                select(User).where(User.email == customer_email)
            )
            user_by_email = user_result.scalar_one_or_none()
            if user_by_email:
                result = await db.execute(
                    select(Subscription).where(Subscription.user_id == user_by_email.id)
                    .order_by(Subscription.created_at.desc())
                )
                sub = result.scalar_one_or_none()

    if not sub:
        return {"ok": True}

    user = await db.get(User, sub.user_id)

    # PAYMENT_STATUS_CHANGED: data.status 로 성공/실패 구분 (2024-06-01 API)
    # 구버전 호환: BILLING_SUCCESS / BILLING_FAILED 이벤트명도 처리
    is_success = (
        event_type == "BILLING_SUCCESS"
        or (event_type == "PAYMENT_STATUS_CHANGED" and payment_status == "DONE")
    )
    is_failed = (
        event_type == "BILLING_FAILED"
        or (event_type == "PAYMENT_STATUS_CHANGED" and payment_status in ("ABORTED", "EXPIRED"))
    )
    # PAYMENT_STATUS_CHANGED + CANCELED: 결제 취소는 구독 비활성화 처리
    is_cancel = (
        event_type in ("BILLING_DELETED",)
        or (event_type == "PAYMENT_STATUS_CHANGED" and payment_status == "CANCELED")
    )

    if is_success:
        sub.status = "active"
        sub.next_billing_at = datetime.utcnow() + timedelta(days=30)
        payment_key = data.get("paymentKey") or data.get("payment", {}).get("paymentKey")
        if payment_key:
            sub.last_payment_key = payment_key
        if user:
            user.plan = "pro"
    elif is_failed:
        sub.status = "inactive"
        sub.cancelled_at = datetime.utcnow()
        if user:
            user.plan = "free"
    elif is_cancel:
        sub.status = "cancelled"
        sub.cancelled_at = datetime.utcnow()
        if user:
            user.plan = "free"

    await db.commit()
    return {"ok": True}


# ── 4. 구독 상태 조회 ─────────────────────────────────────────
@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return SubscriptionResponse(
            plan="free",
            status="inactive",
            amount=0,
            next_billing_at=None,
        )
    return sub


# ── 5. 구독 해지 ──────────────────────────────────────────────
@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활성 구독 없음",
        )

    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    current_user.plan = "free"
    await db.commit()

    return {"message": "구독 해지 완료. 현재 기간 만료 후 Free로 전환됩니다."}


# ── 6. 환불 ──────────────────────────────────────────────────
@router.post("/refund", response_model=RefundResponse)
async def refund_payment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활성 구독 없음",
        )
    if not sub.last_payment_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="환불 가능한 결제 내역이 없습니다",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TOSS_BASE}/payments/{sub.last_payment_key}/cancel",
            headers={
                "Authorization": _toss_auth_header(),
                "Content-Type": "application/json",
            },
            json={"cancelReason": "고객 요청 환불"},
        )

    if resp.status_code != 200:
        logger.error(f"[Toss] 환불 실패 (HTTP {resp.status_code}): {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="환불 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )

    refund_data = resp.json()
    refund_amount = refund_data.get("totalAmount", sub.amount)

    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    current_user.plan = "free"
    await db.commit()

    return RefundResponse(message="환불 완료. 영업일 기준 3~5일 내 처리됩니다.", refund_amount=refund_amount)


# ── 7. 실패 콜백 ──────────────────────────────────────────────
@router.get("/fail")
async def payment_fail(request: Request):
    return {"message": "결제가 취소되었습니다."}
