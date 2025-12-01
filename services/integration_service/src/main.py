import asyncio
import logging
from contextlib import asynccontextmanager

from faststream import FastStream
from faststream.asgi import AsgiFastStream, make_ping_asgi
from faststream.nats import NatsBroker
from src.config import settings
from src.database import engine
from src.handlers.billing_handler import register_handlers

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[logging.StreamHandler()],
)
_log = logging.getLogger(settings.LOGGER)

broker = NatsBroker(settings.NATS_CONNECTION_STR)


@asynccontextmanager
async def lifespan(app):
    _log.info(f"Starting {settings.SERVICE_NAME}...")
    await broker.connect()
    yield
    await broker.close()
    await engine.dispose()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


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

register_handlers(broker)

if __name__ == "__main__":
    asyncio.run(app.run())
