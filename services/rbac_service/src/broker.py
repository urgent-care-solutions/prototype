from faststream.nats import NatsBroker

from src.config import settings

broker = NatsBroker(settings.NATS_CONNECTION_STR)
