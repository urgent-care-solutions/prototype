from fastapi import APIRouter, Query, Path, status
from typing import List, Optional
from uuid import UUID

from app.schemas import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.services.organization_service import OrganizationService
from app.services.role_service import RoleService

router = APIRouter()


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(organization: OrganizationCreate):
    org = await OrganizationService.create_organization(organization)
    await RoleService.initialize_default_roles(org.id)
    return org


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: UUID = Path(...)):
    return await OrganizationService.get_organization(organization_id)


@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    is_active: Optional[bool] = Query(None),
    subscription_tier: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await OrganizationService.list_organizations(
        is_active=is_active, subscription_tier=subscription_tier, skip=skip, limit=limit
    )


@router.put("/organizations/{organization_id}", response_model=OrganizationResponse)
async def update_organization(organization_id: UUID, organization: OrganizationUpdate):
    return await OrganizationService.update_organization(organization_id, organization)


@router.delete(
    "/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_organization(organization_id: UUID):
    await OrganizationService.delete_organization(organization_id)
    return None


@router.get("/organizations/{organization_id}/stats")
async def get_organization_stats(organization_id: UUID):
    return await OrganizationService.get_organization_stats(organization_id)


@router.post("/organizations/{organization_id}/initialize-roles")
async def initialize_organization_roles(organization_id: UUID):
    roles = await RoleService.initialize_default_roles(organization_id)
    return {
        "created_roles": len(roles),
        "roles": [{"id": str(r.id), "name": r.name} for r in roles],
    }
