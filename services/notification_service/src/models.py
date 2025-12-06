import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient = Column(String(255), nullable=False)
    channel = Column(String(10), nullable=False)  # email, sms
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="sent")

    related_resource_type = Column(String(50), nullable=True)
    related_resource_id = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
