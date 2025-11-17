from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models import User, Organization, Role
from app.schemas import UserCreate, UserUpdate
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi import HTTPException, status


class UserService:
    @staticmethod
    async def create_user(user_data: UserCreate) -> User:
        try:
            organization = await Organization.get(id=user_data.organization_id)
            if not organization.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is not active",
                )

            role = await Role.get(id=user_data.role_id)
            if not role.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Role is not active"
                )

            password_hash = User.hash_password(user_data.password)

            user = await User.create(
                organization_id=user_data.organization_id,
                role_id=user_data.role_id,
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_provider=user_data.is_provider,
                provider_npi=user_data.provider_npi,
                phone=user_data.phone,
            )

            return user

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        except DoesNotExist as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization or Role not found",
            )

    @staticmethod
    async def get_user(user_id: UUID) -> User:
        try:
            user = await User.get(id=user_id).prefetch_related("organization", "role")
            return user
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        try:
            user = await User.get(email=email).prefetch_related("organization", "role")
            return user
        except DoesNotExist:
            return None

    @staticmethod
    async def list_users(
        organization_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        query = User.all().prefetch_related("organization", "role")

        if organization_id:
            query = query.filter(organization_id=organization_id)
        if role_id:
            query = query.filter(role_id=role_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)

        users = await query.offset(skip).limit(limit)
        return users

    @staticmethod
    async def update_user(user_id: UUID, user_data: UserUpdate) -> User:
        try:
            user = await User.get(id=user_id)

            update_data = user_data.model_dump(exclude_unset=True)

            if "role_id" in update_data:
                role = await Role.get(id=update_data["role_id"])
                if not role.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Role is not active",
                    )

            for field, value in update_data.items():
                setattr(user, field, value)

            await user.save()
            return user

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User or Role not found"
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    @staticmethod
    async def delete_user(user_id: UUID) -> bool:
        try:
            user = await User.get(id=user_id)
            user.is_active = False
            await user.save()
            return True
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    @staticmethod
    async def verify_user_password(email: str, password: str) -> Optional[User]:
        user = await UserService.get_user_by_email(email)

        if not user:
            return None

        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is locked until {user.account_locked_until}",
            )

        if not user.verify_password(password):
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

            await user.save()
            return None

        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        await user.save()

        return user

    @staticmethod
    async def get_user_permissions(user_id: UUID) -> dict:
        try:
            user = await User.get(id=user_id).prefetch_related("role")
            return user.role.permissions
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
