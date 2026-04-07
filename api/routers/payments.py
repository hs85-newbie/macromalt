import base64
import hashlib
import hmac
import json
import uuid
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.models import Subscription, User
from schemas.schemas import (
    PaymentReadyRequest,
    PaymentReadyResponse,
    SubscriptionResponse,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])

TOSS_BASE = "https://api.tosspayments.com/v1"


def _toss_auth_header() -> str:
    credentials = base64.b64encode(f"{settings.TOSS_SECRET_KEY}:".encode()).decode()
    return f"Basic {credentials}"


def _verify_toss_signature(raw_body: bytes, signature_header: str) -> bool:
    """Toss 웹훅 HMAC-SHA256 서명 검증.

    Toss-Signature 헤더 형식: v1={base64_signature}
    서명 대상: raw request body
    """
    if not settings.TOSS_WEBHOOK_SECRET_KEY:
        # [SEC3] 프로덕션에서는 TOSS_WEBHOOK_SECRET_KEY 환경변수 반드시 설정
        return True  # 개발 환경(키 미설정)에서는 검증 통과

    if not signature_header or not signature_header.startswith("v1="):
        return False

    expected_sig = signature_header[3:]
    computed_sig = base64.b64encode(
        hmac.new(
            settings.TOSS_WEBHOOK_SECRET_KEY.encode(),
            raw_body,
            hashlib.sha256,
        ).digest()
    ).decode()

    return hmac.compare_digest(expected_sig, computed_sig)


# ── 1. 결제 준비 ──────────────────────────────────────────────
@router.post("/ready", response_model=PaymentReadyResponse)
async def payment_ready(
    body: PaymentReadyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer_key = f"macromalt-{current_user.id}-{secrets.token_hex(8)}"
    order_id = f"order-{uuid.uuid4().hex[:16]}"

    # [SEC2 수정] customerKey를 DB에 pending 상태로 저장하여 /confirm에서 DB 검증 가능하게 함
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "pending",
        )
    )
    pending_sub = result.scalar_one_or_none()
    if pending_sub:
        pending_sub.toss_customer_key = customer_key
    else:
        pending_sub = Subscription(
            user_id=current_user.id,
            toss_customer_key=customer_key,
            plan="pro",
            status="pending",
            amount=49900,
        )
        db.add(pending_sub)
    await db.commit()

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

    # [SEC2 수정] customerKey를 DB에서 조회하여 우리 시스템이 발급한 키인지 검증
    # 문자열 파싱으로 user_id를 추출하는 방식 제거 (조작 가능)
    result = await db.execute(
        select(Subscription).where(
            Subscription.toss_customer_key == customer_key,
            Subscription.status == "pending",
        )
    )
    pending_sub = result.scalar_one_or_none()
    if not pending_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 customerKey 또는 이미 처리된 요청",
        )

    user = await db.get(User, pending_sub.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 없음",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"빌링키 발급 실패: {resp.text}",
        )

    data = resp.json()
    billing_key = data["billingKey"]

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"결제 실패: {charge_resp.text}",
        )

    # pending 구독을 active로 전환
    pending_sub.toss_billing_key = billing_key
    pending_sub.status = "active"
    pending_sub.next_billing_at = datetime.now(timezone.utc) + timedelta(days=30)
    user.plan = "pro"
    await db.commit()

    return {"message": "구독 활성화 완료", "plan": "pro"}


# ── 3. Toss 웹훅 수신 ─────────────────────────────────────────
@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()

    # [SEC3 수정] Toss 웹훅 서명 검증 — 미검증 시 가짜 웹훅으로 구독 상태 조작 가능
    toss_signature = request.headers.get("Toss-Signature", "")
    if not _verify_toss_signature(raw_body, toss_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="웹훅 서명 검증 실패",
        )

    body = json.loads(raw_body)
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

    now = datetime.now(timezone.utc)
    if is_success:
        sub.status = "active"
        sub.next_billing_at = now + timedelta(days=30)
        if user:
            user.plan = "pro"
    elif is_failed:
        sub.status = "inactive"
        sub.cancelled_at = now
        if user:
            user.plan = "free"
    elif is_cancel:
        sub.status = "cancelled"
        sub.cancelled_at = now
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
    sub.cancelled_at = datetime.now(timezone.utc)
    current_user.plan = "free"
    await db.commit()

    return {"message": "구독 해지 완료. 현재 기간 만료 후 Free로 전환됩니다."}


# ── 6. 실패 콜백 ──────────────────────────────────────────────
@router.get("/fail")
async def payment_fail(request: Request):
    return {"message": "결제가 취소되었습니다."}
