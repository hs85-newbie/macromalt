from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from models.models import RefreshTokenBlacklist, User
from schemas.schemas import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="유효하지 않은 refresh_token입니다",
)


async def _blacklist_token(db: AsyncSession, token: str, payload: dict) -> None:
    """refresh_token을 블랙리스트에 등록한다."""
    exp_ts = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else datetime.now(timezone.utc)
    db.add(RefreshTokenBlacklist(token_hash=hash_token(token), expires_at=expires_at))


async def _assert_not_blacklisted(db: AsyncSession, token: str) -> None:
    """블랙리스트에 등록된 토큰이면 401을 올린다."""
    result = await db.execute(
        select(RefreshTokenBlacklist).where(
            RefreshTokenBlacklist.token_hash == hash_token(token)
        )
    )
    if result.scalar_one_or_none():
        raise _CREDENTIALS_ERROR


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        plan="free",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise _CREDENTIALS_ERROR
    except JWTError:
        raise _CREDENTIALS_ERROR

    # 블랙리스트 확인
    await _assert_not_blacklisted(db, body.refresh_token)

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise _CREDENTIALS_ERROR

    # 사용된 refresh_token을 블랙리스트에 등록 (토큰 회전)
    await _blacklist_token(db, body.refresh_token, payload)

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        token_type: str = payload.get("type")
        if token_type != "refresh":
            raise _CREDENTIALS_ERROR
    except JWTError:
        raise _CREDENTIALS_ERROR

    # 이미 블랙리스트에 있으면 무시 (멱등 처리)
    result = await db.execute(
        select(RefreshTokenBlacklist).where(
            RefreshTokenBlacklist.token_hash == hash_token(body.refresh_token)
        )
    )
    if not result.scalar_one_or_none():
        await _blacklist_token(db, body.refresh_token, payload)
        await db.commit()
