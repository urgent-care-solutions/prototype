import asyncio
import logging
from contextlib import asynccontextmanager

from faststream import FastStream
from faststream.asgi import AsgiFastStream, make_ping_asgi

import src.handlers.clinic_handler  # noqa: F401
import src.handlers.department_handler  # noqa: F401
import src.handlers.location_handler  # noqa: F401

# Import handlers to register subscribers
import src.handlers.role_handler  # noqa: F401
import src.handlers.user_handler  # noqa: F401
from src.broker import broker
from src.config import settings
from src.database import engine
from src.services.role_service import RoleService

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

    try:
        await RoleService.initialize_default_roles()
    except Exception as e:
        _log.error(f"Error initializing default roles: {e}")

    yield
    await broker.close()
    await engine.dispose()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


async def main() -> None:
    """Entry point for the service."""
    # The app object is defined in src.broker using FastStream
    # We run it using the built-in run functionality or via CLI.
    # Since the Dockerfile calls `uv run main.py`, we run it here.

    app = AsgiFastStream(
        FastStream(
            broker,
            title=settings.SERVICE_NAME,
            version=settings.VERSION,
            description=settings.SERVICE_DESCRIPTION,
            lifespan=lifespan,
        ),
        asgi_routes=[
            (
                "/healthz",
                make_ping_asgi(
                    broker, timeout=1.0, include_in_schema=False
                ),
            )
        ],
    )

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
