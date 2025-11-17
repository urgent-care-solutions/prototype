from fastapi import APIRouter, Query, Path, status
from typing import List, Optional
from uuid import UUID

from app.schemas import RoleCreate, RoleUpdate, RoleResponse
from app.services.role_service import RoleService

router = APIRouter()


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate):
    return await RoleService.create_role(role)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: UUID = Path(...)):
    return await RoleService.get_role(role_id)


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    organization_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await RoleService.list_roles(
        organization_id=organization_id, is_active=is_active, skip=skip, limit=limit
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: UUID, role: RoleUpdate):
    return await RoleService.update_role(role_id, role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: UUID):
    await RoleService.delete_role(role_id)
    return None


@router.post("/organizations/{organization_id}/roles/initialize")
async def initialize_default_roles(organization_id: UUID):
    roles = await RoleService.initialize_default_roles(organization_id)
    return {
        "created_roles": len(roles),
        "roles": [{"id": str(r.id), "name": r.name} for r in roles],
    }
