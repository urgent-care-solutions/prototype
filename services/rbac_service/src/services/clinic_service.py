import logging
from uuid import UUID

from messages import ClinicCreate, ClinicUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_session
from src.models import Clinic

_log = logging.getLogger(settings.LOGGER)


class ClinicService:
    @staticmethod
    async def get_session() -> AsyncSession:
        async for session in get_session():
            return session

    @staticmethod
    async def get_clinic(clinic_id: UUID) -> Clinic | None:
        session = await ClinicService.get_session()
        async with session:
            query = select(Clinic).where(Clinic.id == str(clinic_id))
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def list_clinics() -> list[Clinic]:
        session = await ClinicService.get_session()
        async with session:
            query = select(Clinic)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_clinic(clinic_data: ClinicCreate) -> Clinic:
        session = await ClinicService.get_session()
        async with session:
            db_clinic = Clinic(
                name=clinic_data.name,
                address=clinic_data.address,
                email=clinic_data.email,
                timezone=clinic_data.timezone,
                working_hours=clinic_data.working_hours,
            )
            session.add(db_clinic)
            await session.commit()
            await session.refresh(db_clinic)
            _log.info(f"Created clinic: {db_clinic.id}")
            return db_clinic

    @staticmethod
    async def update_clinic(clinic_id: UUID, clinic_data: ClinicUpdate) -> Clinic:
        session = await ClinicService.get_session()
        async with session:
            query = select(Clinic).where(Clinic.id == str(clinic_id))
            result = await session.execute(query)
            db_clinic = result.scalars().first()

            if not db_clinic:
                raise ValueError(f"Clinic {clinic_id} not found")

            if clinic_data.name:
                db_clinic.name = clinic_data.name
            if clinic_data.address:
                db_clinic.address = clinic_data.address
            if clinic_data.email:
                db_clinic.email = clinic_data.email
            if clinic_data.timezone:
                db_clinic.timezone = clinic_data.timezone
            if clinic_data.working_hours:
                db_clinic.working_hours = clinic_data.working_hours

            await session.commit()
            await session.refresh(db_clinic)
            return db_clinic

    @staticmethod
    async def delete_clinic(clinic_id: UUID) -> Clinic:
        session = await ClinicService.get_session()
        async with session:
            query = select(Clinic).where(Clinic.id == str(clinic_id))
            result = await session.execute(query)
            db_clinic = result.scalars().first()

            if not db_clinic:
                raise ValueError(f"Clinic {clinic_id} not found")

            await session.delete(db_clinic)
            await session.commit()
            _log.info(f"Deleted clinic: {clinic_id}")
            return db_clinic
