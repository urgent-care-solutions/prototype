import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    appointment_id = Column(String(36), nullable=True)

    # CHARGE or REFUND
    type = Column(String(20), nullable=False)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # PENDING, SUCCESS, FAILED
    status = Column(String(20), default="pending")

    # Used for refunds to point to original charge
    reference_id = Column(String(36), nullable=True)

    description = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )
