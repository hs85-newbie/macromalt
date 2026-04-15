from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ── User ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        return v


# ── API Keys ──────────────────────────────────────────────────────────────────

class ApiKeyRequest(BaseModel):
    provider: str
    api_key: str


class ApiKeyResponse(BaseModel):
    provider: str
    is_valid: bool
    last_tested_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── WordPress ─────────────────────────────────────────────────────────────────

class WpSettingsRequest(BaseModel):
    site_url: str
    username: str
    password: str
    category_analysis: int = 2
    category_picks: int = 3
    category_default: int = 1


class WpSettingsResponse(BaseModel):
    site_url: str
    username: str
    is_connected: bool
    last_tested_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Pipeline Settings ─────────────────────────────────────────────────────────

class PipelineSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    slot: Optional[str] = None
    max_posts_per_run: Optional[int] = None
    language: Optional[str] = None


class PipelineSettingsResponse(BaseModel):
    enabled: bool
    slot: Optional[str]
    max_posts_per_run: Optional[int]
    language: Optional[str]

    model_config = {"from_attributes": True}


# ── Pipeline Execute ──────────────────────────────────────────────────────────

class PipelineExecuteRequest(BaseModel):
    slot: str = "morning"


# ── Run Logs ──────────────────────────────────────────────────────────────────

class RunLogResponse(BaseModel):
    id: int
    status: str
    slot: Optional[str]
    triggered_by: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    error_message: Optional[str]
    cost_usd: Optional[float]
    cost_krw: Optional[int]

    model_config = {"from_attributes": True}


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentReadyRequest(BaseModel):
    plan: str = "pro"
    amount: int = 49900


class PaymentReadyResponse(BaseModel):
    checkout_url: str
    customer_key: str
    order_id: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    amount: int
    next_billing_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Published Posts ───────────────────────────────────────────────────────────

class PublishedPostResponse(BaseModel):
    id: int
    wp_post_id: Optional[int]
    wp_post_url: Optional[str]
    title: str
    category: Optional[str]
    published_at: datetime

    model_config = {"from_attributes": True}
