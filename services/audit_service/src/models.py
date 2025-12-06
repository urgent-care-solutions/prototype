import uuid
from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, String, Boolean, JSON, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditEntry(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Traceability
    message_id = Column(String(36), nullable=True)
    request_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)

    # Event Details
    timestamp = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    service_name = Column(String(100), nullable=False)
    success = Column(Boolean, default=True)

    # Using log_metadata to avoid conflict with Base.metadata
    log_metadata = Column(JSON, nullable=True)
