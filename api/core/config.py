from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./local.db"
    JWT_SECRET_KEY: str  # 필수 — 기본값 없음
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    AES_SECRET_KEY: str  # 필수 — 반드시 32바이트, 기본값 없음
    ENVIRONMENT: str = "development"
    TOSS_SECRET_KEY: str  # 필수 — 기본값 없음
    TOSS_CLIENT_KEY: str  # 필수 — 기본값 없음
    RAILWAY_URL: str = "https://macromalt-production.up.railway.app"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
