import logging
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, delete
from shared.messages import AuditLog
from src.database import AsyncSessionLocal
from src.models import AuditEntry
from src.config import settings

_log = logging.getLogger("audit_service")

class LogService:
    @staticmethod
    async def create_log(msg: AuditLog) -> None:
        async with AsyncSessionLocal() as session:
            try:
                entry = AuditEntry(
                    message_id=str(msg.message_id),
                    request_id=str(msg.request_id) if msg.request_id else None,
                    user_id=str(msg.user_id) if msg.user_id else None,
                    timestamp=msg.timestamp,
                    action=msg.action,
                    resource_type=msg.resource_type,
                    resource_id=str(msg.resource_id) if msg.resource_id else None,
                    service_name=msg.service_name,
                    success=msg.success,
                    log_metadata=msg.metadata
                )
                session.add(entry)
                await session.commit()
                _log.info(f"Logged {msg.action} on {msg.resource_type} by {msg.service_name}")
            except Exception as e:
                _log.error(f"Failed to save audit log: {e}")
                await session.rollback()

    @staticmethod
    async def cleanup_old_logs() -> int:
        """Deletes logs older than the configured retention period."""
        cutoff_date = datetime.now(tz=UTC) - timedelta(days=settings.RETENTION_DAYS)
        _log.info(f"Running retention cleanup for logs older than {cutoff_date}")
        
        async with AsyncSessionLocal() as session:
            try:
                stmt = delete(AuditEntry).where(AuditEntry.timestamp < cutoff_date)
                result = await session.execute(stmt)
                await session.commit()
                deleted_count = result.rowcount
                _log.info(f"Retention cleanup complete. Deleted {deleted_count} records.")
                return deleted_count
            except Exception as e:
                _log.error(f"Error during retention cleanup: {e}")
                return 0
