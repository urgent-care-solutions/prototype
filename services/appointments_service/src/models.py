import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ProviderSchedule(Base):
    __tablename__ = "provider_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), nullable=False)
    # 0 = Monday, 6 = Sunday
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    provider_id = Column(String(36), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # initial, follow_up, telemedicine
    appointment_type = Column(String(50), nullable=False)

    # scheduled, canceled, completed, no_show
    status = Column(String(20), default="scheduled")

    reason = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )
