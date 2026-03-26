import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db, AsyncSessionLocal
from api.core.deps import get_current_user
from api.models.models import PublishedPost, RunLog, User
from api.schemas.schemas import (
    PipelineExecuteRequest,
    PublishedPostResponse,
    RunLogResponse,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


async def _dummy_pipeline_run(run_log_id: int):
    """
    M2에서 실제 파이프라인으로 교체 예정.
    현재는 3초 후 success로 업데이트.
    """
    await asyncio.sleep(3)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(RunLog).where(RunLog.id == run_log_id))
        run_log = result.scalar_one_or_none()
        if run_log:
            run_log.status = "success"
            run_log.finished_at = datetime.now(timezone.utc)
            db.add(run_log)
            await db.commit()


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

    background_tasks.add_task(_dummy_pipeline_run, run_log.id)

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
