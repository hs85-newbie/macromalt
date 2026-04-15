from pydantic_settings import BaseSettings

# 개발 환경 기본값 — 프로덕션에서 이 값이 그대로 사용되면 즉시 오류 발생
_DEV_SECRETS = {
    "JWT_SECRET_KEY": "dev-secret-change-in-production",
    "AES_SECRET_KEY": "dev-aes-key-32bytes-change-prod!",
    "TOSS_SECRET_KEY": "test_sk_placeholder",
    "TOSS_CLIENT_KEY": "test_ck_placeholder",
}


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./local.db"
    JWT_SECRET_KEY: str = _DEV_SECRETS["JWT_SECRET_KEY"]
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AES_SECRET_KEY: str = _DEV_SECRETS["AES_SECRET_KEY"]  # 반드시 32바이트
    ENVIRONMENT: str = "development"
    TOSS_SECRET_KEY: str = _DEV_SECRETS["TOSS_SECRET_KEY"]
    TOSS_CLIENT_KEY: str = _DEV_SECRETS["TOSS_CLIENT_KEY"]
    RAILWAY_URL: str = "https://macromalt-production.up.railway.app"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()

# 프로덕션에서 개발용 기본값 사용 시 즉시 오류 발생
if settings.ENVIRONMENT == "production":
    _using_dev = [k for k, dev_val in _DEV_SECRETS.items() if getattr(settings, k) == dev_val]
    if _using_dev:
        raise ValueError(
            f"프로덕션에서 개발용 기본값 사용 금지 — 환경변수 설정 필요: {', '.join(_using_dev)}"
        )
