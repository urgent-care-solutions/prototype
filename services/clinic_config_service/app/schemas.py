from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=200)
    type: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "America/New_York"
    subscription_tier: str = "standard"


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    subscription_tier: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)


class RoleCreate(RoleBase):
    organization_id: UUID


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    id: UUID
    organization_id: UUID
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    is_provider: bool = False
    provider_npi: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=12)
    organization_id: UUID
    role_id: UUID

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[UUID] = None
    is_provider: Optional[bool] = None
    provider_npi: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    organization_id: UUID
    role_id: UUID
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClinicBase(BaseModel):
    name: str = Field(..., max_length=200)
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    timezone: str = "America/New_York"
    working_hours: Dict[str, Any] = Field(default_factory=dict)


class ClinicCreate(ClinicBase):
    organization_id: UUID


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    working_hours: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ClinicResponse(ClinicBase):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationBase(BaseModel):
    name: str = Field(..., max_length=200)
    type: str = Field(..., max_length=50)
    address: Dict[str, Any]
    phone: Optional[str] = None
    timezone: str = "America/New_York"


class LocationCreate(LocationBase):
    organization_id: UUID
    clinic_id: Optional[UUID] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    id: UUID
    organization_id: UUID
    clinic_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=200)


class DepartmentCreate(DepartmentBase):
    organization_id: UUID
    location_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    location_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    organization_id: UUID
    location_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: Optional[str] = None
    timestamp: datetime
