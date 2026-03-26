from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./local.db"
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    AES_SECRET_KEY: str = "dev-aes-key-32bytes-change-prod!"  # 반드시 32바이트
    ENVIRONMENT: str = "development"

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
