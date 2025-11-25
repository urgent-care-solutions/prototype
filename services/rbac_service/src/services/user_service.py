import logging
from uuid import UUID

from pydantic import EmailStr, SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.messages import UserCreate, UserUpdate
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import User

_log = logging.getLogger(settings.LOGGER)


class UserService:
    @staticmethod
    async def get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            return session

    @staticmethod
    async def get_user_by_id(user_id: UUID) -> User | None:
        _log.debug(f"Attempting to get user {user_id}")
        async with AsyncSessionLocal() as session:
            query = select(User).where(User.id == str(user_id))
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def get_user_by_email(email: EmailStr) -> User | None:
        _log.debug(f"Attempting to get user {email}")
        async with AsyncSessionLocal() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def create_user(user: UserCreate) -> User:
        _log.debug(f"Attempting to create user {user.user_id}")
        async with AsyncSessionLocal() as session:
            db_user = User(
                role_id=user.role_id,
                email=user.email,
                password_hash=User.hash_password(
                    user.password.get_secret_value()
                ),
                first_name=getattr(user, "first_name", ""),
                last_name=getattr(user, "last_name", ""),
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            return db_user

    @staticmethod
    async def update_user(user_data: UserUpdate) -> User:
        _log.debug(f"Attempting to update user {user_data.user_id}")
        user = await UserService.get_user_by_id(UUID(user_data.user_id))
        if not user:
            raise ValueError(f"User {user_data.user_id} not found")

        async with AsyncSessionLocal() as session:
            query = select(User).where(
                User.id == str(user_data.user_id)
            )
            result = await session.execute(query)
            db_user = result.scalars().first()

            if not db_user:
                raise ValueError(f"User {user_data.user_id} not found")

            for field, value in user_data.model_dump(
                exclude_unset=True
            ).items():
                if field not in [
                    "user_id",
                    "message_id",
                    "timestamp",
                    "request_id",
                ]:
                    setattr(db_user, field, value)

            await session.commit()
            await session.refresh(db_user)
            return db_user

    @staticmethod
    async def delete_user(user_id: UUID) -> User:
        _log.debug(f"Attempting to delete user {user_id}")
        async with AsyncSessionLocal() as session:
            query = select(User).where(User.id == str(user_id))
            result = await session.execute(query)
            user = result.scalars().first()

            if not user:
                raise ValueError(f"User {user_id} not found")

            await session.delete(user)
            await session.commit()
            return user

    @staticmethod
    async def list_users(
        role_id: UUID | None = None, *, is_active: bool | None = None
    ) -> list[User]:
        _log.debug("Attempting to list all users")
        async with AsyncSessionLocal() as session:
            query = select(User)

            if role_id:
                query = query.where(User.role_id == str(role_id))

            if is_active is not None:
                query = query.where(User.is_active == is_active)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def verify_user_password(
        email: EmailStr, password: SecretStr
    ) -> User | None:
        _log.debug(f"Verifying user {email} password")
        user = await UserService.get_user_by_email(email)
        if user and user.verify_password(password.get_secret_value()):
            return user
        return None

    @staticmethod
    async def get_user_permissions(user_id: UUID) -> dict:
        _log.debug(f"Attempting to get user {user_id} permissions")
        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        async with AsyncSessionLocal() as session:
            query = select(User).where(User.id == str(user_id))
            result = await session.execute(query)
            user = result.scalars().first()

            if user and user.role:
                return user.role.permissions
            return {}
