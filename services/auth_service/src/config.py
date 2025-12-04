from pathlib import Path

import toml
from pydantic_settings import BaseSettings, SettingsConfigDict

THIS_DIR = Path(__file__).parent


class Settings(BaseSettings):
    SERVICE_NAME: str
    SERVICE_DESCRIPTION: str = (
        "Handles User Authentication and Session Management"
    )
    VERSION: str

    # NATS
    NATS_CONNECTION_STR: str = "nats://localhost:4222"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    # Auth Settings
    SESSION_TTL_SECONDS: int = 3600  # 1 hour
    LOGGER: str = "rich"

    model_config = SettingsConfigDict(
        env_file=THIS_DIR.parent / ".env",
        env_prefix="PHI__AUTH__",
        env_file_encoding="utf8",
    )


with Path(THIS_DIR.parent / "pyproject.toml").open("r") as f:
    pp_data = toml.load(f)

settings = Settings(
    SERVICE_NAME=pp_data["project"]["name"],
    VERSION=pp_data["project"]["version"],
)
