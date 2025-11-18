import logging
from typing import Optional

import redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.client = None

    def connect(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
            self.client.ping()
            logger.info(
                f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
            )
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Token blacklist will not work."
            )
            self.client = None

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from Redis")

    def set_refresh_token(self, jti: str, user_id: str, ttl_seconds: int):
        if not self.client:
            return
        try:
            self.client.setex(f"refresh_token:{jti}", ttl_seconds, user_id)
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")

    def get_refresh_token(self, jti: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            return self.client.get(f"refresh_token:{jti}")
        except Exception as e:
            logger.error(f"Failed to get refresh token: {e}")
            return None

    def delete_refresh_token(self, jti: str):
        if not self.client:
            return
        try:
            self.client.delete(f"refresh_token:{jti}")
        except Exception as e:
            logger.error(f"Failed to delete refresh token: {e}")

    def blacklist_token(self, token: str, ttl_seconds: int):
        if not self.client:
            return
        try:
            self.client.setex(f"blacklist:{token}", ttl_seconds, "1")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")

    def is_token_blacklisted(self, token: str) -> bool:
        if not self.client:
            return False
        try:
            return self.client.exists(f"blacklist:{token}") > 0
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False


redis_client = RedisClient()
