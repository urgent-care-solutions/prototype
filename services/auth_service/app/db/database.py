import asyncpg
from app.config import settings
import logging

logger = logging.getLogger(__name__)

db_pool = None


async def init_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL, min_size=2, max_size=10, command_timeout=60
        )
        logger.info("Database pool created")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        raise


async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


async def get_db():
    if not db_pool:
        raise Exception("Database not initialized")
    async with db_pool.acquire() as conn:
        yield conn
