from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./local.db"
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    AES_SECRET_KEY: str = "dev-aes-key-32bytes-change-prod!"  # 반드시 32바이트
    ENVIRONMENT: str = "development"
    TOSS_SECRET_KEY: str = "test_sk_placeholder"
    TOSS_CLIENT_KEY: str = "test_ck_placeholder"
    TOSS_WEBHOOK_SECRET_KEY: str = ""  # Toss 웹훅 서명 검증 키 (Railway Variables에서 설정)
    RAILWAY_URL: str = "https://macromalt-production.up.railway.app"
    # 프로덕션에서는 ALLOWED_ORIGINS=https://your-domain.com 으로 환경변수 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
    ]

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
