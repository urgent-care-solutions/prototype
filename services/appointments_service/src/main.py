import asyncio
import logging
from contextlib import asynccontextmanager

from faststream import FastStream
from faststream.nats import NatsBroker

from src.config import settings
from src.database import engine
from src.handlers.appointment_handler import register_handlers

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

    # Ideally run migrations here or in a separate init container
    # For now, we assume migrations are run externally or via a script

    yield
    await broker.close()
    await engine.dispose()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


app = FastStream(
    broker,
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description=settings.SERVICE_DESCRIPTION,
    lifespan=lifespan,
)

register_handlers(broker)

if __name__ == "__main__":
    asyncio.run(app.run())
