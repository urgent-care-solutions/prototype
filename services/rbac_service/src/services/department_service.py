import logging
from uuid import UUID

from messages import DepartmentCreate, DepartmentUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_session
from src.models import Department

_log = logging.getLogger(settings.LOGGER)


class DepartmentService:
    @staticmethod
    async def get_session() -> AsyncSession:
        async for session in get_session():
            return session

    @staticmethod
    async def get_department(dep_id: UUID) -> Department | None:
        session = await DepartmentService.get_session()
        async with session:
            query = select(Department).where(Department.id == str(dep_id))
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def list_departments(location_id: UUID = None) -> list[Department]:
        session = await DepartmentService.get_session()
        async with session:
            query = select(Department)
            if location_id:
                query = query.where(Department.location_id == str(location_id))
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_department(dep_data: DepartmentCreate) -> Department:
        session = await DepartmentService.get_session()
        async with session:
            db_dep = Department(
                location_id=str(dep_data.location_id),
                name=dep_data.name,
                type=dep_data.type,
                floor=dep_data.floor,
                wing=dep_data.wing,
                phone=dep_data.phone,
                email=dep_data.email,
                manager_id=str(dep_data.manager_id) if dep_data.manager_id else None,
                is_active=dep_data.is_active,
                operating_hours=dep_data.operating_hours,
            )
            session.add(db_dep)
            await session.commit()
            await session.refresh(db_dep)
            _log.info(f"Created department: {db_dep.id} in location {db_dep.location_id}")
            return db_dep

    @staticmethod
    async def update_department(dep_id: UUID, dep_data: DepartmentUpdate) -> Department:
        session = await DepartmentService.get_session()
        async with session:
            query = select(Department).where(Department.id == str(dep_id))
            result = await session.execute(query)
            db_dep = result.scalars().first()

            if not db_dep:
                raise ValueError(f"Department {dep_id} not found")

            if dep_data.name:
                db_dep.name = dep_data.name
            if dep_data.type:
                db_dep.type = dep_data.type
            if dep_data.floor:
                db_dep.floor = dep_data.floor
            if dep_data.wing:
                db_dep.wing = dep_data.wing
            if dep_data.phone:
                db_dep.phone = dep_data.phone
            if dep_data.email:
                db_dep.email = dep_data.email
            if dep_data.manager_id:
                db_dep.manager_id = str(dep_data.manager_id)
            if dep_data.is_active is not None:
                db_dep.is_active = dep_data.is_active
            if dep_data.operating_hours:
                db_dep.operating_hours = dep_data.operating_hours

            await session.commit()
            await session.refresh(db_dep)
            return db_dep

    @staticmethod
    async def delete_department(dep_id: UUID) -> Department:
        session = await DepartmentService.get_session()
        async with session:
            query = select(Department).where(Department.id == str(dep_id))
            result = await session.execute(query)
            db_dep = result.scalars().first()

            if not db_dep:
                raise ValueError(f"Department {dep_id} not found")

            await session.delete(db_dep)
            await session.commit()
            _log.info(f"Deleted department: {dep_id}")
            return db_dep
