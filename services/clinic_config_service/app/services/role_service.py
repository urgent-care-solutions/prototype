from typing import List, Optional
from uuid import UUID
from app.models import Role, Organization
from app.schemas import RoleCreate, RoleUpdate
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi import HTTPException, status


class RoleService:
    @staticmethod
    async def create_role(role_data: RoleCreate) -> Role:
        try:
            organization = await Organization.get(id=role_data.organization_id)
            if not organization.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is not active",
                )

            role = await Role.create(
                organization_id=role_data.organization_id,
                name=role_data.name,
                description=role_data.description,
                permissions=role_data.permissions,
            )

            return role

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists in this organization",
            )
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

    @staticmethod
    async def get_role(role_id: UUID) -> Role:
        try:
            role = await Role.get(id=role_id).prefetch_related("organization")
            return role
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

    @staticmethod
    async def list_roles(
        organization_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Role]:
        query = Role.all().prefetch_related("organization")

        if organization_id:
            query = query.filter(organization_id=organization_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)

        roles = await query.offset(skip).limit(limit)
        return roles

    @staticmethod
    async def update_role(role_id: UUID, role_data: RoleUpdate) -> Role:
        try:
            role = await Role.get(id=role_id)

            if role.is_system_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot modify system roles",
                )

            update_data = role_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(role, field, value)

            await role.save()
            return role

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists in this organization",
            )

    @staticmethod
    async def delete_role(role_id: UUID) -> bool:
        try:
            role = await Role.get(id=role_id)

            if role.is_system_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete system roles",
                )

            users_count = await role.users.all().count()
            if users_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete role with {users_count} assigned users",
                )

            role.is_active = False
            await role.save()
            return True

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

    @staticmethod
    async def initialize_default_roles(organization_id: UUID) -> List[Role]:
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
        ]

        created_roles = []
        for role_data in default_roles:
            try:
                role = await Role.create(
                    organization_id=organization_id,
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system_role=True,
                )
                created_roles.append(role)
            except IntegrityError:
                pass

        return created_roles
