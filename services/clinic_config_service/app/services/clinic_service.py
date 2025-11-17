from typing import List, Optional
from uuid import UUID
from app.models import Clinic, Organization, Location, Department, User
from app.schemas import (
    ClinicCreate,
    ClinicUpdate,
    LocationCreate,
    LocationUpdate,
    DepartmentCreate,
    DepartmentUpdate,
)
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi import HTTPException, status


class ClinicService:
    @staticmethod
    async def create_clinic(clinic_data: ClinicCreate) -> Clinic:
        try:
            organization = await Organization.get(id=clinic_data.organization_id)
            if not organization.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is not active",
                )

            clinic = await Clinic.create(
                organization_id=clinic_data.organization_id or uuid.uuid4(),
                name=clinic_data.name,
                address=clinic_data.address,
                phone=clinic_data.phone,
                email=clinic_data.email,
                timezone=clinic_data.timezone,
                working_hours=clinic_data.working_hours,
            )

            return clinic

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

    @staticmethod
    async def get_clinic(clinic_id: UUID) -> Clinic:
        try:
            clinic = await Clinic.get(id=clinic_id).prefetch_related("organization")
            return clinic
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found"
            )

    @staticmethod
    async def list_clinics(
        organization_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Clinic]:
        query = Clinic.all().prefetch_related("organization")

        if organization_id:
            query = query.filter(organization_id=organization_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)

        clinics = await query.offset(skip).limit(limit)
        return clinics

    @staticmethod
    async def update_clinic(clinic_id: UUID, clinic_data: ClinicUpdate) -> Clinic:
        try:
            clinic = await Clinic.get(id=clinic_id)

            update_data = clinic_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(clinic, field, value)

            await clinic.save()
            return clinic

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found"
            )

    @staticmethod
    async def delete_clinic(clinic_id: UUID) -> bool:
        try:
            clinic = await Clinic.get(id=clinic_id)
            clinic.is_active = False
            await clinic.save()
            return True
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found"
            )

    @staticmethod
    async def get_clinic_hours(clinic_id: UUID, date: str) -> dict:
        try:
            clinic = await Clinic.get(id=clinic_id)
            return {
                "clinic_id": str(clinic.id),
                "clinic_name": clinic.name,
                "working_hours": clinic.working_hours,
                "timezone": clinic.timezone,
            }
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found"
            )


class LocationService:
    @staticmethod
    async def create_location(location_data: LocationCreate) -> Location:
        try:
            organization = await Organization.get(id=location_data.organization_id)
            if not organization.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is not active",
                )

            if location_data.clinic_id:
                await Clinic.get(id=location_data.clinic_id)

            location = await Location.create(
                organization_id=location_data.organization_id,
                clinic_id=location_data.clinic_id,
                name=location_data.name,
                type=location_data.type,
                address=location_data.address,
                phone=location_data.phone,
                timezone=location_data.timezone,
            )

            return location

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization or Clinic not found",
            )

    @staticmethod
    async def list_locations(
        organization_id: Optional[UUID] = None,
        clinic_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Location]:
        query = Location.all().prefetch_related("organization", "clinic")

        if organization_id:
            query = query.filter(organization_id=organization_id)
        if clinic_id:
            query = query.filter(clinic_id=clinic_id)

        locations = await query.offset(skip).limit(limit)
        return locations


class DepartmentService:
    @staticmethod
    async def create_department(department_data: DepartmentCreate) -> Department:
        try:
            organization = await Organization.get(id=department_data.organization_id)
            if not organization.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is not active",
                )

            if department_data.location_id:
                await Location.get(id=department_data.location_id)

            if department_data.manager_id:
                await User.get(id=department_data.manager_id)

            department = await Department.create(
                organization_id=department_data.organization_id,
                location_id=department_data.location_id,
                manager_id=department_data.manager_id,
                name=department_data.name,
            )

            return department

        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization, Location, or Manager not found",
            )

    @staticmethod
    async def list_departments(
        organization_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Department]:
        query = Department.all().prefetch_related("organization", "location", "manager")

        if organization_id:
            query = query.filter(organization_id=organization_id)
        if location_id:
            query = query.filter(location_id=location_id)

        departments = await query.offset(skip).limit(limit)
        return departments
