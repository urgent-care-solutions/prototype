from fastapi import APIRouter, Query, Path, status
from typing import List, Optional
from uuid import UUID

from app.schemas import (
    ClinicCreate,
    ClinicUpdate,
    ClinicResponse,
    LocationCreate,
    LocationResponse,
    DepartmentCreate,
    DepartmentResponse,
)
from app.services.clinic_service import (
    ClinicService,
    LocationService,
    DepartmentService,
)

router = APIRouter()


@router.post(
    "/clinics", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED
)
async def create_clinic(clinic: ClinicCreate):
    return await ClinicService.create_clinic(clinic)


@router.get("/clinics/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(clinic_id: UUID = Path(...)):
    return await ClinicService.get_clinic(clinic_id)


@router.get("/clinics", response_model=List[ClinicResponse])
async def list_clinics(
    organization_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await ClinicService.list_clinics(
        organization_id=organization_id, is_active=is_active, skip=skip, limit=limit
    )


@router.put("/clinics/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(clinic_id: UUID, clinic: ClinicUpdate):
    return await ClinicService.update_clinic(clinic_id, clinic)


@router.delete("/clinics/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinic(clinic_id: UUID):
    await ClinicService.delete_clinic(clinic_id)
    return None


@router.get("/clinics/{clinic_id}/hours")
async def get_clinic_hours(clinic_id: UUID, date: str = Query(None)):
    return await ClinicService.get_clinic_hours(clinic_id, date)


@router.post(
    "/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED
)
async def create_location(location: LocationCreate):
    return await LocationService.create_location(location)


@router.get("/locations", response_model=List[LocationResponse])
async def list_locations(
    organization_id: Optional[UUID] = Query(None),
    clinic_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await LocationService.list_locations(
        organization_id=organization_id, clinic_id=clinic_id, skip=skip, limit=limit
    )


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(department: DepartmentCreate):
    return await DepartmentService.create_department(department)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    organization_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    return await DepartmentService.list_departments(
        organization_id=organization_id, location_id=location_id, skip=skip, limit=limit
    )
