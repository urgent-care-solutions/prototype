import logging
from uuid import uuid4

from pydantic import EmailStr, SecretStr

from shared.messages import UserCreate, UserUpdate
from src.models import User

_log = logging.getLogger("rich")


# todo: finish implementation
class UserService:
    @staticmethod
    async def get_user_by_id(id: uuid4) -> User:
        _log.debug(f"Attempting to get user {id}")
        pass

    @staticmethod
    async def get_user_by_email(email: EmailStr) -> User:
        _log.debug(f"Attempting to get user {email}")
        pass

    @staticmethod
    async def create_user(user: UserCreate) -> User:
        _log.debug(f"Attempting to create user {user.user_id}")
        pass

    @staticmethod
    async def update_user(user_data: UserUpdate) -> User:
        _log.debug(f"Attempting to update user {user_data.user_id}")
        user = await UserService.get_user_by_id(user_data.user_id)
        pass

    @staticmethod
    async def delete_user(user: User) -> User:
        _log.debug(f"Attempting to delete user {user.user_id}")
        pass

    @staticmethod
    async def list_users(role_id: uuid4 | None = None, *, is_active: bool | None = None) -> list[User]:
        _log.debug("Attempting to list all users")
        pass

    @staticmethod
    async def verify_user_password(email: EmailStr, password: SecretStr) -> User:
        _log.debug(f"Verifying user {email} password")
        pass

    @staticmethod
    async def get_user_permissions(user_id: uuid4) -> User:
        _log.debug(f"Attempting to get user {user_id} permissions")
        pass
