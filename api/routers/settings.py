from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import get_current_user
from api.core.security import decrypt_api_key, encrypt_api_key
from api.models.models import User, UserApiKey, UserPipelineSettings, UserWpSettings
from api.schemas.schemas import (
    ApiKeyRequest,
    ApiKeyResponse,
    PipelineSettingsRequest,
    PipelineSettingsResponse,
    WpSettingsRequest,
    WpSettingsResponse,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── API Keys ──────────────────────────────────────────────────────────────────

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    return keys


@router.post("/api-keys", response_model=ApiKeyResponse)
async def save_api_key(
    body: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key_enc, iv = encrypt_api_key(body.api_key)

    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == current_user.id,
            UserApiKey.provider == body.provider,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.key_enc = key_enc
        existing.iv = iv
        existing.is_valid = True
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        new_key = UserApiKey(
            user_id=current_user.id,
            provider=body.provider,
            key_enc=key_enc,
            iv=iv,
            is_valid=True,
        )
        db.add(new_key)
        await db.commit()
        await db.refresh(new_key)
        return new_key


@router.post("/api-keys/{provider}/test")
async def test_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.user_id == current_user.id,
            UserApiKey.provider == provider,
        )
    )
    key_row = result.scalar_one_or_none()
    if not key_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{provider} API 키가 등록되어 있지 않습니다",
        )

    plain_key = decrypt_api_key(key_row.key_enc, key_row.iv)
    is_valid = False
    message = ""

    try:
        if provider == "openai":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {plain_key}"},
                )
            is_valid = resp.status_code == 200
            message = "유효한 키입니다" if is_valid else f"OpenAI 응답: {resp.status_code}"
        elif provider == "gemini":
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={plain_key}"
                )
            is_valid = resp.status_code == 200
            message = "유효한 키입니다" if is_valid else f"Gemini 응답: {resp.status_code}"
        else:
            # 기타 provider는 저장 성공으로 간주
            is_valid = True
            message = f"{provider} 키가 저장되어 있습니다 (자동 검증 미지원)"
    except Exception as e:
        is_valid = False
        message = str(e)

    # 테스트 결과 업데이트
    key_row.is_valid = is_valid
    key_row.last_tested_at = datetime.now(timezone.utc)
    db.add(key_row)
    await db.commit()

    return {"is_valid": is_valid, "message": message}


# ── WordPress ─────────────────────────────────────────────────────────────────

@router.get("/wordpress", response_model=WpSettingsResponse)
async def get_wp_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserWpSettings).where(UserWpSettings.user_id == current_user.id)
    )
    wp = result.scalar_one_or_none()
    if not wp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WordPress 설정이 없습니다",
        )
    return wp


@router.post("/wordpress", response_model=WpSettingsResponse)
async def save_wp_settings(
    body: WpSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    password_enc, iv = encrypt_api_key(body.password)

    result = await db.execute(
        select(UserWpSettings).where(UserWpSettings.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.site_url = body.site_url
        existing.username = body.username
        existing.password_enc = password_enc
        existing.iv = iv
        existing.category_analysis = body.category_analysis
        existing.category_picks = body.category_picks
        existing.category_default = body.category_default
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        wp = UserWpSettings(
            user_id=current_user.id,
            site_url=body.site_url,
            username=body.username,
            password_enc=password_enc,
            iv=iv,
            category_analysis=body.category_analysis,
            category_picks=body.category_picks,
            category_default=body.category_default,
            is_connected=False,
        )
        db.add(wp)
        await db.commit()
        await db.refresh(wp)
        return wp


@router.post("/wordpress/test")
async def test_wp_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserWpSettings).where(UserWpSettings.user_id == current_user.id)
    )
    wp = result.scalar_one_or_none()
    if not wp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WordPress 설정이 없습니다",
        )

    plain_password = decrypt_api_key(wp.password_enc, wp.iv)
    is_connected = False
    message = ""

    try:
        site_url = wp.site_url.rstrip("/")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{site_url}/wp-json/wp/v2/posts?per_page=1",
                auth=(wp.username, plain_password),
            )
        is_connected = resp.status_code == 200
        message = "연결 성공" if is_connected else f"WordPress 응답: {resp.status_code}"
    except Exception as e:
        is_connected = False
        message = str(e)

    wp.is_connected = is_connected
    wp.last_tested_at = datetime.now(timezone.utc)
    db.add(wp)
    await db.commit()

    return {"is_connected": is_connected, "message": message}


# ── Pipeline Settings ─────────────────────────────────────────────────────────

@router.get("/pipeline", response_model=PipelineSettingsResponse)
async def get_pipeline_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPipelineSettings).where(UserPipelineSettings.user_id == current_user.id)
    )
    ps = result.scalar_one_or_none()
    if not ps:
        # 기본값으로 생성
        ps = UserPipelineSettings(user_id=current_user.id)
        db.add(ps)
        await db.commit()
        await db.refresh(ps)
    return ps


@router.patch("/pipeline", response_model=PipelineSettingsResponse)
async def update_pipeline_settings(
    body: PipelineSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPipelineSettings).where(UserPipelineSettings.user_id == current_user.id)
    )
    ps = result.scalar_one_or_none()
    if not ps:
        ps = UserPipelineSettings(user_id=current_user.id)

    if body.enabled is not None:
        ps.enabled = body.enabled
    if body.slot is not None:
        ps.slot = body.slot
    if body.max_posts_per_run is not None:
        ps.max_posts_per_run = body.max_posts_per_run
    if body.language is not None:
        ps.language = body.language
    ps.updated_at = datetime.now(timezone.utc)

    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return ps
