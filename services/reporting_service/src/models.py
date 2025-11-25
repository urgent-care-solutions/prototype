from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReportingAppointment(Base):
    """Read-optimized view of appointments"""

    __tablename__ = "reporting_appointments"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), nullable=False)
    provider_id = Column(String(36), nullable=False)

    # Store dates as native datetime for easy range queries
    start_time = Column(DateTime, nullable=False)
    date_only = Column(Date, nullable=False, index=True)

    appointment_type = Column(String(50), nullable=False)
    status = Column(String(20), default="scheduled")

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(tz=UTC))


class ReportingTransaction(Base):
    """Read-optimized view of financial transactions"""

    __tablename__ = "reporting_transactions"

    id = Column(String(36), primary_key=True)
    patient_id = Column(String(36), nullable=False)

    type = Column(String(20), nullable=False)  # CHARGE or REFUND
    amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)

    transaction_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))


class ReportingPatient(Base):
    """Read-optimized view of patient demographics"""

    __tablename__ = "reporting_patients"

    id = Column(String(36), primary_key=True)
    is_active = Column(Boolean, default=True)
    registration_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
