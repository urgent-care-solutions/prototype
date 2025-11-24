import logging
from uuid import UUID

from sqlalchemy import select

from shared.messages import PatientCreate, PatientUpdate
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Patient

_log = logging.getLogger(settings.LOGGER)


class PatientService:
    @staticmethod
    async def get_patient(patient_id: UUID) -> Patient | None:
        async with AsyncSessionLocal() as session:
            query = select(Patient).where(Patient.id == str(patient_id))
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def get_patient_by_mrn(mrn: str) -> Patient | None:
        async with AsyncSessionLocal() as session:
            query = select(Patient).where(Patient.mrn == mrn)
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def create_patient(data: PatientCreate) -> Patient:
        # Check for MRN uniqueness
        existing = await PatientService.get_patient_by_mrn(data.mrn)
        if existing:
            raise ValueError(
                f"Patient with MRN {data.mrn} already exists."
            )

        async with AsyncSessionLocal() as session:
            db_patient = Patient(
                first_name=data.first_name,
                last_name=data.last_name,
                mrn=data.mrn,
                email=data.email,
                insurance=data.insurance.model_dump()
                if data.insurance
                else None,
                is_active=data.is_active,
            )
            session.add(db_patient)
            await session.commit()
            await session.refresh(db_patient)
            _log.info(f"Created patient: {db_patient.id}")
            return db_patient

    @staticmethod
    async def update_patient(data: PatientUpdate) -> Patient:
        async with AsyncSessionLocal() as session:
            query = select(Patient).where(
                Patient.id == str(data.patient_id)
            )
            result = await session.execute(query)
            db_patient = result.scalars().first()

            if not db_patient:
                raise ValueError(f"Patient {data.patient_id} not found")

            if data.first_name:
                db_patient.first_name = data.first_name
            if data.last_name:
                db_patient.last_name = data.last_name
            if data.email:
                db_patient.email = data.email
            if data.insurance:
                db_patient.insurance = data.insurance.model_dump()
            if data.is_active is not None:
                db_patient.is_active = data.is_active

            await session.commit()
            await session.refresh(db_patient)
            _log.info(f"Updated patient: {db_patient.id}")
            return db_patient

    @staticmethod
    async def delete_patient(patient_id: UUID) -> Patient:
        async with AsyncSessionLocal() as session:
            query = select(Patient).where(Patient.id == str(patient_id))
            result = await session.execute(query)
            db_patient = result.scalars().first()

            if not db_patient:
                raise ValueError(f"Patient {patient_id} not found")

            await session.delete(db_patient)
            await session.commit()
            _log.info(f"Deleted patient: {patient_id}")
            return db_patient
