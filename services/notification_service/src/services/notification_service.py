import asyncio
import logging
from uuid import UUID

from src.config import settings
from src.database import AsyncSessionLocal
from src.models import NotificationHistory

_log = logging.getLogger(settings.LOGGER)


class NotificationService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        content: str,
        resource_type: str = None,
        resource_id: UUID = None,
    ) -> NotificationHistory:
        # Simulate Network Delay
        await asyncio.sleep(0.1)

        # MOCK SENDING
        _log.info(f"📧 [MOCK EMAIL] To: {to_email} | Subject: {subject}")
        _log.info(f"   Body: {content}")

        async with AsyncSessionLocal() as session:
            record = NotificationHistory(
                recipient=to_email,
                channel="email",
                subject=subject,
                content=content,
                status="sent",
                related_resource_type=resource_type,
                related_resource_id=str(resource_id) if resource_id else None,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def send_sms(
        to_phone: str,
        content: str,
        resource_type: str = None,
        resource_id: UUID = None,
    ) -> NotificationHistory:
        # Simulate Network Delay
        await asyncio.sleep(0.1)

        # MOCK SENDING
        _log.info(f"📱 [MOCK SMS] To: {to_phone} | Message: {content}")

        async with AsyncSessionLocal() as session:
            record = NotificationHistory(
                recipient=to_phone,
                channel="sms",
                subject=None,
                content=content,
                status="sent",
                related_resource_type=resource_type,
                related_resource_id=str(resource_id) if resource_id else None,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record
