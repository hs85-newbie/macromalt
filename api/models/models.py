from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    plan = Column(String(20), nullable=False, default="free")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")
    wp_settings = relationship("UserWpSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pipeline_settings = relationship("UserPipelineSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    run_logs = relationship("RunLog", back_populates="user", cascade="all, delete-orphan")
    published_posts = relationship("PublishedPost", back_populates="user", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    toss_billing_key = Column(String(255))
    toss_customer_key = Column(String(255))
    plan = Column(String(20), nullable=False, default="pro")
    status = Column(String(20), nullable=False, default="inactive")
    amount = Column(Integer, nullable=False, default=49900)
    next_billing_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="subscriptions")


class UserApiKey(Base):
    __tablename__ = "user_api_keys"
    __table_args__ = (UniqueConstraint("user_id", "provider"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(30), nullable=False)
    key_enc = Column(Text, nullable=False)
    iv = Column(String(64), nullable=False)
    is_valid = Column(Boolean, nullable=False, default=True)
    last_tested_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="api_keys")


class UserWpSettings(Base):
    __tablename__ = "user_wp_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    site_url = Column(String(500), nullable=False)
    username = Column(String(100), nullable=False)
    password_enc = Column(Text, nullable=False)
    iv = Column(String(64), nullable=False)
    category_analysis = Column(Integer, default=2)
    category_picks = Column(Integer, default=3)
    category_default = Column(Integer, default=1)
    is_connected = Column(Boolean, nullable=False, default=False)
    last_tested_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="wp_settings")


class UserPipelineSettings(Base):
    __tablename__ = "user_pipeline_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=False)
    slot = Column(String(20), default="morning")
    max_posts_per_run = Column(Integer, default=3)
    language = Column(String(10), default="ko")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    user = relationship("User", back_populates="pipeline_settings")


class RunLog(Base):
    __tablename__ = "run_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    slot = Column(String(20))
    triggered_by = Column(String(20), default="manual")
    started_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    finished_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    cost_usd = Column(Numeric(10, 6), default=0)
    cost_krw = Column(Integer, default=0)

    user = relationship("User", back_populates="run_logs")
    published_posts = relationship("PublishedPost", back_populates="run_log")


class RefreshTokenBlacklist(Base):
    __tablename__ = "refresh_token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # SHA-256(refresh_token) — 원문 저장 금지
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    run_log_id = Column(Integer, ForeignKey("run_logs.id"))
    wp_post_id = Column(Integer)
    wp_post_url = Column(Text)
    title = Column(Text, nullable=False)
    category = Column(String(50))
    published_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    user = relationship("User", back_populates="published_posts")
    run_log = relationship("RunLog", back_populates="published_posts")
