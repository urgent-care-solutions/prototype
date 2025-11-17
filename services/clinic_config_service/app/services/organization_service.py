from typing import List, Optional
from uuid import UUID
from app.models import Organization
from app.schemas import OrganizationCreate, OrganizationUpdate
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi import HTTPException, status


class OrganizationService:
    @staticmethod
    async def create_organization(org_data: OrganizationCreate) -> Organization:
        try:
            organization = await Organization.create(
                name=org_data.name,
                type=org_data.type,
                tax_id=org_data.tax_id,
                address=org_data.address,
                settings=org_data.settings,
                timezone=org_data.timezone,
                subscription_tier=org_data.subscription_tier,
            )
            return organization
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists",
            )

    @staticmethod
    async def get_organization(org_id: UUID) -> Organization:
        try:
            organization = await Organization.get(id=org_id)
            return organization
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

    @staticmethod
    async def list_organizations(
        is_active: Optional[bool] = None,
        subscription_tier: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Organization]:
        query = Organization.all()

        if is_active is not None:
            query = query.filter(is_active=is_active)
        if subscription_tier:
            query = query.filter(subscription_tier=subscription_tier)

        organizations = await query.offset(skip).limit(limit)
        return organizations

    @staticmethod
    async def update_organization(
        org_id: UUID, org_data: OrganizationUpdate
    ) -> Organization:
        try:
            organization = await Organization.get(id=org_id)

            update_data = org_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(organization, field, value)

            await organization.save()
            return organization

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists",
            )

    @staticmethod
    async def delete_organization(org_id: UUID) -> bool:
        try:
            organization = await Organization.get(id=org_id)
            organization.is_active = False
            await organization.save()
            return True
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

    @staticmethod
    async def get_organization_stats(org_id: UUID) -> dict:
        try:
            organization = await Organization.get(id=org_id).prefetch_related(
                "users", "roles", "clinics", "locations", "departments"
            )

            users_count = await organization.users.all().count()
            roles_count = await organization.roles.all().count()
            clinics_count = await organization.clinics.all().count()
            locations_count = await organization.locations.all().count()

            return {
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "users_count": users_count,
                "roles_count": roles_count,
                "clinics_count": clinics_count,
                "locations_count": locations_count,
                "subscription_tier": organization.subscription_tier,
                "is_active": organization.is_active,
            }
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
