from faststream import FastStream
from faststream.nats import NatsBroker

from src.config import settings

broker = NatsBroker(settings.NATS_CONNECTION_STR)

app = FastStream(
    broker,
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description=settings.SERVICE_DESCRIPTION,
)
