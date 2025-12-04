from pathlib import Path

import toml
from pydantic_settings import BaseSettings, SettingsConfigDict

THIS_DIR = Path(__file__).parent


class Settings(BaseSettings):
    SERVICE_NAME: str
    SERVICE_DESCRIPTION: str = "Handles System Audit Logs"
    VERSION: str
    NATS_CONNECTION_STR: str = "nats://localhost:4222"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/phi_audit"

    # 6 years in days (approx)
    RETENTION_DAYS: int = 365 * 6

    model_config = SettingsConfigDict(
        env_file=THIS_DIR.parent / ".env",
        env_prefix="PHI__AUDIT__",
        env_file_encoding="utf8",
    )


with Path(THIS_DIR.parent / "pyproject.toml").open("r") as f:
    pp_data = toml.load(f)

settings = Settings(
    SERVICE_NAME=pp_data["project"]["name"],
    VERSION=pp_data["project"]["version"],
)
