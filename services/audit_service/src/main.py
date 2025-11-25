import asyncio
import logging
from contextlib import asynccontextmanager
from faststream import FastStream
from shared.messages import AuditLog
from src.broker import broker
from src.config import settings
from src.database import engine
from src.services.log_service import LogService

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[logging.StreamHandler()],
)
_log = logging.getLogger(settings.SERVICE_NAME)

async def retention_policy_task():
    """Background task to clean up logs periodically (every 24 hours)."""
    while True:
        try:
            # Wait 1 minute before first run to let app startup completely
            await asyncio.sleep(60) 
            await LogService.cleanup_old_logs()
            # Sleep for 24 hours
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            break
        except Exception as e:
            _log.error(f"Error in retention task: {e}")
            await asyncio.sleep(3600) # Retry in an hour if failed

@asynccontextmanager
async def lifespan(app):
    _log.info(f"Starting {settings.SERVICE_NAME}...")
    await broker.connect()
    
    # Start retention background task
    task = asyncio.create_task(retention_policy_task())
    
    yield
    
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
        
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

# Subscribe to all audit logs using wildcard
@broker.subscriber("audit.log.>")
async def handle_audit_log(msg: AuditLog):
    await LogService.create_log(msg)

if __name__ == "__main__":
    asyncio.run(app.run())
