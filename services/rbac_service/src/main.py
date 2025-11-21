import asyncio
import logging
from contextlib import asynccontextmanager

from faststream import FastStream

import src.handlers.clinic_handler  # noqa: F401
import src.handlers.department_handler  # noqa: F401
import src.handlers.location_handler  # noqa: F401

# Import handlers to register subscribers
import src.handlers.role_handler  # noqa: F401
import src.handlers.user_handler  # noqa: F401
from src.broker import broker
from src.config import settings
from src.database import engine

# Setup logging
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[logging.StreamHandler()],
)

_log = logging.getLogger(settings.LOGGER)


@asynccontextmanager
async def lifespan(app):
    _log.info(f"Starting {settings.SERVICE_NAME}...")
    await broker.connect()
    yield
    await broker.close()
    await engine.dispose()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


async def main() -> None:
    """Entry point for the service."""
    # The app object is defined in src.broker using FastStream
    # We run it using the built-in run functionality or via CLI.
    # Since the Dockerfile calls `uv run main.py`, we run it here.

    app = FastStream(
        broker,
        title=settings.SERVICE_NAME,
        version=settings.VERSION,
        description=settings.SERVICE_DESCRIPTION,
        lifespan=lifespan,
    )

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
