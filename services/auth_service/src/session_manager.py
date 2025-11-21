import json
import logging
import uuid

import redis.asyncio as redis
from shared.messages import UserPasswordVerified

from src.config import settings

_log = logging.getLogger(settings.LOGGER)


class SessionManager:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD, decode_responses=True
        )

    async def create_session(self, user_data: UserPasswordVerified) -> str:
        """Generates a token and stores user session in Redis."""
        token = str(uuid.uuid4())
        key = f"session:{token}"

        session_data = {
            "user_id": str(user_data.user_id),
            "role_id": user_data.role_id,
            "email": user_data.email,
            "is_active": user_data.is_active,
        }

        try:
            await self.redis.set(key, json.dumps(session_data), ex=settings.SESSION_TTL_SECONDS)
            _log.debug(f"Session created for user {user_data.email}")
            return token
        except Exception as e:
            _log.error(f"Failed to create session in Redis: {e}")
            raise

    async def get_session(self, token: str) -> dict | None:
        """Retrieves session data from Redis and refreshes TTL."""
        key = f"session:{token}"
        try:
            data = await self.redis.get(key)
            if data:
                # Refresh TTL on activity
                await self.redis.expire(key, settings.SESSION_TTL_SECONDS)
                return json.loads(data)
            return None
        except Exception as e:
            _log.error(f"Redis error during get_session: {e}")
            return None

    async def delete_session(self, token: str) -> bool:
        """Removes session from Redis."""
        key = f"session:{token}"
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            _log.error(f"Redis error during delete_session: {e}")
            return False

    async def close(self):
        await self.redis.close()
