import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgres://clinicdev:devsecurepassword123@localhost:5432/clinicphi",
    )

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "dev-jwt-secret-key-change-for-production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRY_DAYS: int = 7

    PORT: int = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
