import logging
from uuid import UUID

from messages import LocationCreate, LocationUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_session
from src.models import Location

_log = logging.getLogger(settings.LOGGER)


class LocationService:
    @staticmethod
    async def get_session() -> AsyncSession:
        async for session in get_session():
            return session

    @staticmethod
    async def get_location(location_id: UUID) -> Location | None:
        session = await LocationService.get_session()
        async with session:
            query = select(Location).where(
                Location.id == str(location_id)
            )
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def list_locations(clinic_id: UUID = None) -> list[Location]:
        session = await LocationService.get_session()
        async with session:
            query = select(Location)
            if clinic_id:
                query = query.where(
                    Location.clinic_id == str(clinic_id)
                )
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_location(loc_data: LocationCreate) -> Location:
        session = await LocationService.get_session()
        async with session:
            db_location = Location(
                clinic_id=str(loc_data.clinic_id),
                name=loc_data.name,
                type=loc_data.type,
                address=loc_data.address,
                phone=loc_data.phone,
                email=loc_data.email,
                manager_id=str(loc_data.manager_id)
                if loc_data.manager_id
                else None,
                is_active=loc_data.is_active,
            )
            session.add(db_location)
            await session.commit()
            await session.refresh(db_location)
            _log.info(
                f"Created location: {db_location.id} for clinic {db_location.clinic_id}"
            )
            return db_location

    @staticmethod
    async def update_location(
        location_id: UUID, loc_data: LocationUpdate
    ) -> Location:
        session = await LocationService.get_session()
        async with session:
            query = select(Location).where(
                Location.id == str(location_id)
            )
            result = await session.execute(query)
            db_location = result.scalars().first()

            if not db_location:
                raise ValueError(f"Location {location_id} not found")

            if loc_data.name:
                db_location.name = loc_data.name
            if loc_data.type:
                db_location.type = loc_data.type
            if loc_data.address:
                db_location.address = loc_data.address
            if loc_data.phone:
                db_location.phone = loc_data.phone
            if loc_data.email:
                db_location.email = loc_data.email
            if loc_data.manager_id:
                db_location.manager_id = str(loc_data.manager_id)
            if loc_data.is_active is not None:
                db_location.is_active = loc_data.is_active

            await session.commit()
            await session.refresh(db_location)
            return db_location

    @staticmethod
    async def delete_location(location_id: UUID) -> Location:
        session = await LocationService.get_session()
        async with session:
            query = select(Location).where(
                Location.id == str(location_id)
            )
            result = await session.execute(query)
            db_location = result.scalars().first()

            if not db_location:
                raise ValueError(f"Location {location_id} not found")

            await session.delete(db_location)
            await session.commit()
            _log.info(f"Deleted location: {location_id}")
            return db_location
