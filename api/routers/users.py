from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import get_current_user
from api.core.security import hash_password
from api.models.models import User
from api.schemas.schemas import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        current_user.name = body.name
    if body.password is not None:
        current_user.password_hash = hash_password(body.password)
    current_user.updated_at = datetime.now(timezone.utc)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
