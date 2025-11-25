import asyncio
import logging
from typing import Type, TypeVar

from faststream.nats import NatsBroker
from pydantic import BaseModel

from src.config import settings

_log = logging.getLogger(settings.LOGGER)

T = TypeVar("T", bound=BaseModel)


class NatsClient:
    def __init__(self):
        self.broker = NatsBroker(settings.NATS_CONNECTION_STR)

    async def connect(self):
        await self.broker.connect()
        _log.info("NATS Client connected")

    async def close(self):
        await self.broker.close()
        _log.info("NATS Client closed")

    async def request(
        self,
        subject: str,
        message: BaseModel,
        response_model: Type[T],
        timeout: float = 5.0,
    ) -> T:
        """
        Sends a request via NATS and awaits a response.
        """
        try:
            # Publish with RPC pattern (Request-Reply)
            response = await self.broker.publish(
                message, subject=subject, rpc=True, timeout=timeout
            )

            # FastStream automatically decodes to dict or model if typed,
            # but we explicitly validate to ensure type safety in Gateway
            if isinstance(response, dict):
                return response_model.model_validate(response)
            return response
        except asyncio.TimeoutError:
            _log.error(f"NATS Timeout on subject {subject}")
            raise Exception("Service unavailable or timed out")
        except Exception as e:
            _log.error(f"NATS Error on {subject}: {e}")
            raise Exception(f"Internal communication error: {str(e)}")


# Global instance
nats_client = NatsClient()
