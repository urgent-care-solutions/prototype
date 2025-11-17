import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import redis.asyncio as redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class RedisTokenManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise Exception("Redis is required for auth service")

    async def close(self):
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection closed")

    async def store_refresh_token(self, token: str, user_id: str) -> bool:
        try:
            token_id = str(uuid.uuid4())
            token_data = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "token_id": token_id,
            }

            key = f"refresh_token:{token}"
            ttl_seconds = settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60

            await self.redis_client.setex(key, ttl_seconds, json.dumps(token_data))

            await self.redis_client.sadd(f"user_sessions:{user_id}", token)

            logger.info(f"Stored refresh token for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
            return False

    async def get_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            key = f"refresh_token:{token}"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get refresh token: {e}")
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        try:
            token_data = await self.get_refresh_token(token)
            if token_data:
                user_id = token_data["user_id"]
                await self.redis_client.srem(f"user_sessions:{user_id}", token)

            await self.redis_client.delete(f"refresh_token:{token}")
            logger.info("Refresh token revoked")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False

    async def blacklist_access_token(self, token: str, exp_timestamp: int) -> bool:
        try:
            ttl = exp_timestamp - int(datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await self.redis_client.setex(f"blacklist:{token}", ttl, "1")
                logger.info("Access token blacklisted")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_token_blacklisted(self, token: str) -> bool:
        try:
            result = await self.redis_client.get(f"blacklist:{token}")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> list:
        try:
            sessions = await self.redis_client.smembers(f"user_sessions:{user_id}")
            return list(sessions)
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []

    async def revoke_all_user_sessions(self, user_id: str) -> bool:
        try:
            sessions = await self.get_user_sessions(user_id)
            for token in sessions:
                await self.redis_client.delete(f"refresh_token:{token}")

            await self.redis_client.delete(f"user_sessions:{user_id}")
            logger.info(f"Revoked all sessions for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke all sessions: {e}")
            return False


token_manager = RedisTokenManager()
