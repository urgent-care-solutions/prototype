import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Clinic Config Service"
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

    PORT: int = int(os.getenv("CLINIC_CONFIG_SERVICE_PORT", "8007"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50057"))
    AUDIT_SERVICE_URL: Optional[str] = os.getenv("AUDIT_SERVICE_URL")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
