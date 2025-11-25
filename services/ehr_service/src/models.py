import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    appointment_id = Column(String(36), nullable=True, unique=True)
    patient_id = Column(String(36), nullable=False)
    provider_id = Column(String(36), nullable=False)
    date = Column(DateTime, nullable=False)

    # SOAP Notes
    subjective = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)

    # Stored as JSON list of objects {code: str, description: str}
    diagnosis_codes = Column(JSON, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    vitals = relationship("Vitals", back_populates="encounter")
    prescriptions = relationship(
        "Prescription", back_populates="encounter"
    )


class Vitals(Base):
    __tablename__ = "vitals"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    encounter_id = Column(
        String(36), ForeignKey("encounters.id"), nullable=True
    )
    patient_id = Column(String(36), nullable=False)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(tz=UTC))

    encounter = relationship("Encounter", back_populates="vitals")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    encounter_id = Column(
        String(36), ForeignKey("encounters.id"), nullable=True
    )
    patient_id = Column(String(36), nullable=False)
    provider_id = Column(String(36), nullable=False)

    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(
        String(20), default="active"
    )  # active, completed, cancelled

    created_at = Column(DateTime, default=lambda: datetime.now(tz=UTC))

    encounter = relationship(
        "Encounter", back_populates="prescriptions"
    )
