import logging
from uuid import UUID

from shared.messages import RoleCreate, RoleUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Role

_log = logging.getLogger(settings.LOGGER)


class RoleService:
    @staticmethod
    async def get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            return session

    @staticmethod
    async def create_role(role_data: RoleCreate) -> Role:
        _log.debug("Attempting to create role")
        async with AsyncSessionLocal() as session:
            db_role = Role(
                name=role_data.name,
                description=role_data.description,
                permissions=role_data.permissions,
            )
            session.add(db_role)
            await session.commit()
            await session.refresh(db_role)
            return db_role

    @staticmethod
    async def get_role(role_id: UUID) -> Role:
        _log.debug(f"Attempting to get role {role_id}")
        async with AsyncSessionLocal() as session:
            query = select(Role).where(Role.id == str(role_id))
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def list_roles(
        *, is_active: bool | None = None
    ) -> list[Role]:
        _log.debug("Attempting to list all roles")
        if is_active is not None:
            _log.debug("Filtering roles by active status")
        else:
            _log.debug("No active status filter applied")
        async with AsyncSessionLocal() as session:
            query = select(Role)

            if is_active is not None:
                query = query.where(Role.is_active == is_active)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_role(role_id: UUID, role_data: RoleUpdate) -> Role:
        _log.debug(f"Attempting to update role {role_id}")
        role = await RoleService.get_role(role_id)
        if not role:
            msg = f"Role {role_id} not found"
            raise ValueError(msg)

        async with AsyncSessionLocal() as session:
            query = select(Role).where(Role.id == str(role_id))
            result = await session.execute(query)
            db_role = result.scalars().first()

            if not db_role:
                raise ValueError(f"Role {role_id} not found")

            for field, value in role_data.model_dump(
                exclude_unset=True
            ).items():
                if field not in [
                    "id",
                    "message_id",
                    "timestamp",
                    "request_id",
                ]:
                    setattr(db_role, field, value)

            session.add(db_role)
            await session.commit()
            await session.refresh(db_role)
            return db_role

    @staticmethod
    async def delete_role(role_id: UUID) -> Role:
        _log.debug(f"Attempting to delete role {role_id}")
        async with AsyncSessionLocal() as session:
            query = select(Role).where(Role.id == str(role_id))
            result = await session.execute(query)
            db_role = result.scalars().first()

            if not db_role:
                raise ValueError(f"Role {role_id} not found")

            await session.delete(db_role)
            await session.commit()
            return db_role

    @staticmethod
    async def initialize_default_roles() -> list[Role]:
        _log.debug("Initializing default roles")
        default_roles = [
            {
                "name": "Admin",
                "description": "Full system configuration and user management",
                "permissions": {
                    "patients": ["read", "write", "delete"],
                    "appointments": ["read", "write", "delete"],
                    "billing": ["read", "write", "delete"],
                    "reports": ["read", "export"],
                    "users": ["read", "write", "delete"],
                    "settings": ["read", "write"],
                },
            },
            {
                "name": "Physician",
                "description": "Full EHR access and patient management",
                "permissions": {
                    "patients": ["read", "write"],
                    "appointments": ["read", "write"],
                    "ehr": ["read", "write"],
                    "prescriptions": ["read", "write"],
                    "billing": ["read"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Nurse",
                "description": "Vital signs and rooming access",
                "permissions": {
                    "patients": ["read"],
                    "appointments": ["read"],
                    "ehr": ["read", "write_vitals"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Front Desk",
                "description": "Scheduling and patient registration",
                "permissions": {
                    "patients": ["read", "write_demographics"],
                    "appointments": ["read", "write"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Biller",
                "description": "Claims management and billing",
                "permissions": {
                    "patients": ["read"],
                    "billing": ["read", "write"],
                    "claims": ["read", "write"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Accountant",
                "description": "Financial data and payments",
                "permissions": {
                    "billing": ["read"],
                    "payments": ["read", "write"],
                    "reports": ["read", "export"],
                },
            },
            {
                "name": "Patient",
                "description": "Access to personal health portal, appointments, and records",
                "permissions": {
                    "patients": ["read"],  # Read own demographics
                    "appointments": [
                        "read",
                        "write",
                    ],  # Schedule/View appointments
                    "medical_records": ["read"],  # View own history
                    "billing": ["read"],  # View own bills
                },
            },
        ]

        async with AsyncSessionLocal() as session:
            roles = []
            for role_data in default_roles:
                query = select(Role).where(
                    Role.name == role_data["name"]
                )
                result = await session.execute(query)
                existing_role = result.scalars().first()
                if not existing_role:
                    db_role = Role(
                        name=role_data["name"],
                        description=role_data["description"],
                        permissions=role_data["permissions"],
                    )
                    session.add(db_role)
                    await session.commit()
                    await session.refresh(db_role)
                    roles.append(db_role)
                else:
                    roles.append(existing_role)
            return roles
