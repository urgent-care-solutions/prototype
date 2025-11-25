from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

THIS_DIR = Path(__file__).parent


class Settings(BaseSettings):
    SERVICE_NAME: str = "api-gateway"
    VERSION: str = "0.1.0"
    NATS_CONNECTION_STR: str = "nats://nats:4222"
    LOGGER: str = "rich"

    model_config = SettingsConfigDict(
        env_file=THIS_DIR.parent / ".env",
        env_prefix="PHI__GATEWAY__",
        env_file_encoding="utf8",
    )


settings = Settings()
