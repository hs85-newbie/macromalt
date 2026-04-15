import concurrent.futures
import sys
import os
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, AsyncSessionLocal
from core.deps import get_current_user
from core.security import decrypt_api_key
from models.models import PublishedPost, RunLog, User, UserApiKey, UserWpSettings
from schemas.schemas import (
    PipelineExecuteRequest,
    PublishedPostResponse,
    RunLogResponse,
)

# macromalt 루트 경로를 sys.path에 추가 (api/ 패키지에서 main.py 임포트용)
_PIPELINE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _PIPELINE_ROOT not in sys.path:
    sys.path.insert(0, _PIPELINE_ROOT)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


async def _build_user_context(user_id: int, slot: str, run_log_id: int, session: AsyncSession):
    """DB에서 사용자 설정을 읽어 UserContext를 생성한다."""
    from design.user_context import UserContext

    # API 키 조회 및 복호화
    keys: dict = {}
    result = await session.execute(
        select(UserApiKey).where(UserApiKey.user_id == user_id)
    )
    for key_row in result.scalars():
        keys[key_row.provider] = decrypt_api_key(key_row.key_enc, key_row.iv)

    # WP 설정 조회
    wp_result = await session.execute(
        select(UserWpSettings).where(UserWpSettings.user_id == user_id)
    )
    wp = wp_result.scalar_one_or_none()

    # 사용자 조회
    user = await session.get(User, user_id)

    wp_password = None
    if wp:
        wp_password = decrypt_api_key(wp.password_enc, wp.iv)

    return UserContext(
        user_id=user_id,
        user_email=user.email if user else "",
        openai_api_key=keys.get("openai"),
        gemini_api_key=keys.get("gemini"),
        dart_api_key=keys.get("dart"),
        bok_api_key=keys.get("bok"),
        fred_api_key=keys.get("fred"),
        krx_api_key=keys.get("krx"),
        unsplash_access_key=keys.get("unsplash"),
        wp_url=wp.site_url if wp else None,
        wp_username=wp.username if wp else None,
        wp_password=wp_password,
        wp_category_analysis=wp.category_analysis if wp else 2,
        wp_category_picks=wp.category_picks if wp else 3,
        wp_category_default=wp.category_default if wp else 1,
        slot=slot,
        run_log_id=run_log_id,
    )


def _run_pipeline_sync(ctx) -> None:
    """동기 래퍼: 스레드풀에서 실제 파이프라인을 실행한다."""
    from main import run_pipeline
    run_pipeline(ctx)


async def _execute_pipeline_task(run_log_id: int, user_id: int, slot: str) -> None:
    """BackgroundTask에서 실행되는 실제 파이프라인."""
    async with AsyncSessionLocal() as session:
        run_log = await session.get(RunLog, run_log_id)
        if not run_log:
            return
        try:
            ctx = await _build_user_context(user_id, slot, run_log_id, session)

            missing = ctx.validate()
            if missing:
                raise ValueError(f"설정 누락: {missing}")

            # 파이프라인은 동기 함수이므로 스레드풀에서 실행
            loop = __import__("asyncio").get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, _run_pipeline_sync, ctx)

            run_log.status = "success"
            run_log.finished_at = datetime.now(timezone.utc)
        except Exception as e:
            run_log.status = "failed"
            run_log.error_message = str(e)
            run_log.finished_at = datetime.now(timezone.utc)
        await session.commit()


@router.post("/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_pipeline(
    body: PipelineExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 이미 실행 중인지 확인
    result = await db.execute(
        select(RunLog).where(
            RunLog.user_id == current_user.id,
            RunLog.status == "running",
        )
    )
    running = result.scalar_one_or_none()
    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 파이프라인이 실행 중입니다",
        )

    run_log = RunLog(
        user_id=current_user.id,
        status="running",
        slot=body.slot,
        triggered_by="manual",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run_log)
    await db.commit()
    await db.refresh(run_log)

    background_tasks.add_task(
        _execute_pipeline_task, run_log.id, current_user.id, body.slot
    )

    return {"run_log_id": run_log.id, "message": "파이프라인 실행이 시작되었습니다"}


@router.get("/runs", response_model=List[RunLogResponse])
async def get_run_logs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RunLog)
        .where(RunLog.user_id == current_user.id)
        .order_by(RunLog.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=RunLogResponse)
async def get_run_log(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RunLog).where(
            RunLog.id == run_id,
            RunLog.user_id == current_user.id,
        )
    )
    run_log = result.scalar_one_or_none()
    if not run_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="실행 이력을 찾을 수 없습니다",
        )
    return run_log


@router.get("/posts", response_model=List[PublishedPostResponse])
async def get_published_posts(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PublishedPost)
        .where(PublishedPost.user_id == current_user.id)
        .order_by(PublishedPost.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
