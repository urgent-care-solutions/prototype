import uuid
from datetime import date, datetime, time, timezone
from typing import Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
)

UTC = timezone.utc


class BaseMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: UUID4 = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC)
    )
    user_id: UUID4 | None = None
    request_id: UUID4 | None = None


class BaseRole(BaseMessage):
    id: UUID4 = Field(default_factory=uuid.uuid4)


class RoleRead(BaseRole):
    pass


class RoleReaded(RoleRead):
    success: bool = True


class RoleCreate(BaseRole):
    name: str
    description: str | None = None
    permissions: dict[str, any] = Field(...)


class RoleCreated(RoleCreate):
    success: bool = True


class RoleUpdate(BaseRole):
    pass


class RoleUpdated(RoleUpdate):
    success: bool = True


class RoleDelete(BaseRole):
    pass


class RoleDeleted(RoleDelete):
    success: bool = True


class UserBase(BaseMessage):
    role_id: str
    email: EmailStr


class UserRead(UserBase):
    pass


class UserReaded(UserBase):
    success: bool = True


class UserPasswordVerify(BaseMessage):
    email: EmailStr
    password: SecretStr


class UserPasswordVerified(BaseMessage):
    success: bool = True
    user_id: UUID4 | None = None
    role_id: str | None = None
    email: EmailStr | None = None
    is_active: bool = False


class UserList(UserBase):
    is_active: bool | None = None


class UserListed(UserList):
    success: bool = True


class UserCreate(UserBase):
    password: SecretStr


class UserCreated(UserBase):
    success: bool = True


class UserUpdate(UserBase):
    pass


class UserUpdated(UserBase):
    success: bool = True


class UserDelete(UserBase):
    pass


class UserDeleted(UserBase):
    success: bool = True


class ClinicBase(BaseMessage):
    name: str
    address: dict[str, any] | None = None
    email: EmailStr | None = None
    timezone: str = "America/New_York"
    working_hours: dict[str, any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ClinicRead(ClinicBase):
    clinic_id: UUID4


class ClinicReaded(ClinicRead):
    success: bool = True


class ClinicCreate(ClinicBase):
    pass


class ClinicCreated(ClinicCreate):
    success: bool = True


class ClinicUpdate(ClinicBase):
    clinic_id: UUID4
    name: str | None = None


class ClinicUpdated(ClinicUpdate):
    success: bool = True


class ClinicDelete(ClinicBase):
    clinic_id: UUID4


class ClinicDeleted(ClinicDelete):
    success: bool = True


class DepartmentBase(BaseMessage):
    location_id: UUID4
    name: str
    type: str
    floor: str | None = None
    wing: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    manager_id: UUID4 | None = None
    is_active: bool = True
    operating_hours: dict[str, any] | None = None


class DepartmentRead(DepartmentBase):
    department_id: UUID4


class DepartmentReaded(DepartmentRead):
    success: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentCreated(DepartmentCreate):
    success: bool = True


class DepartmentUpdate(BaseModel):
    department_id: UUID4
    name: str | None = None
    type: str | None = None
    floor: str | None = None
    wing: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    manager_id: UUID4 | None = None
    is_active: bool | None = None
    operating_hours: dict[str, any] | None = None


class DepartmentUpdated(DepartmentUpdate):
    success: bool = True


class DepartmentDelete(DepartmentBase):
    pass


class DepartmentDeleted(DepartmentDelete):
    success: bool = True


class LocationBase(BaseMessage):
    clinic_id: UUID4
    name: str
    type: str
    address: dict[str, any]
    phone: str | None = None
    email: EmailStr | None = None
    manager_id: UUID4 | None = None
    is_active: bool = True


class LocationRead(BaseModel):
    location_id: UUID4


class LocationReaded(LocationBase):
    success: bool = True


class LocationCreate(LocationBase):
    pass


class LocationCreated(LocationBase):
    success: bool = True


class LocationUpdate(BaseModel):
    location_id: UUID4
    name: str | None = None
    type: str | None = None
    address: dict[str, any] | None = None
    phone: str | None = None
    email: EmailStr | None = None
    manager_id: UUID4 | None = None
    is_active: bool | None = None


class LocationUpdated(LocationBase):
    id: UUID4


class LocationDelete(BaseMessage):
    location_id: UUID4


class LocationDeleted(BaseMessage):
    location_id: UUID4
    success: bool = True


class AuthLoginRequest(BaseMessage):
    email: EmailStr
    password: SecretStr


class AuthLoginResponse(BaseMessage):
    success: bool
    token: str | None = None
    user_id: UUID4 | None = None
    role_id: str | None = None
    error: str | None = None


class AuthVerifyRequest(BaseMessage):
    token: str


class AuthVerifyResponse(BaseMessage):
    success: bool
    user_id: UUID4 | None = None
    role_id: str | None = None
    email: EmailStr | None = None
    is_active: bool = False


class AuthLogoutRequest(BaseMessage):
    token: str


class AuthLogoutResponse(BaseMessage):
    success: bool


class InsuranceData(BaseModel):
    provider_name: str
    policy_number: str


class PatientBase(BaseMessage):
    first_name: str
    last_name: str
    mrn: str
    email: EmailStr | None = None
    insurance: InsuranceData | None = None
    is_active: bool = True


class PatientCreate(PatientBase):
    pass


class PatientCreated(PatientBase):
    id: UUID4
    success: bool = True


class PatientRead(BaseMessage):
    patient_id: UUID4


class PatientReaded(PatientBase):
    id: UUID4
    success: bool = True


class PatientUpdate(BaseMessage):
    patient_id: UUID4
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    insurance: InsuranceData | None = None
    is_active: bool | None = None


class PatientUpdated(PatientBase):
    id: UUID4
    success: bool = True


class PatientDelete(BaseMessage):
    patient_id: UUID4


class PatientDeleted(BaseMessage):
    patient_id: UUID4
    success: bool = True


class AppointmentType(BaseModel):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    TELEMEDICINE = "telemedicine"


class ScheduleBase(BaseMessage):
    provider_id: UUID4
    day_of_week: int = Field(
        ..., ge=0, le=6, description="0=Monday, 6=Sunday"
    )
    start_time: time
    end_time: time
    is_active: bool = True


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleCreated(ScheduleBase):
    id: UUID4
    success: bool = True


class ScheduleRead(BaseMessage):
    provider_id: UUID4


class ScheduleList(BaseModel):
    schedules: list[ScheduleCreated]


class AvailabilityRequest(BaseMessage):
    provider_id: UUID4
    date: date


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    available: bool


class AvailabilityResponse(BaseMessage):
    provider_id: UUID4
    date: date
    slots: list[TimeSlot]


class AppointmentBase(BaseMessage):
    patient_id: UUID4
    provider_id: UUID4
    start_time: datetime
    appointment_type: Literal["initial", "follow_up", "telemedicine"]
    reason: str | None = None
    status: Literal["scheduled", "canceled", "completed", "no_show"] = (
        "scheduled"
    )


class AppointmentCreate(BaseMessage):
    patient_id: UUID4
    provider_id: UUID4
    start_time: datetime
    appointment_type: Literal["initial", "follow_up", "telemedicine"]
    reason: str | None = None


class AppointmentCreated(AppointmentBase):
    id: UUID4
    end_time: datetime
    success: bool = True
    error: str | None = None


class AppointmentCancel(BaseMessage):
    appointment_id: UUID4
    reason: str | None = None


class AppointmentCanceled(BaseMessage):
    appointment_id: UUID4
    success: bool = True


class AppointmentRead(BaseMessage):
    appointment_id: UUID4


class AppointmentReaded(AppointmentBase):
    id: UUID4
    end_time: datetime
    success: bool = True


class AuditLog(BaseMessage):
    action: Literal["CREATE", "READ", "UPDATE", "DELETE"] = Field(...)
    resource_type: Literal[
        "patient",
        "user",
        "appointment",
        "role",
        "clinic",
        "department",
        "location",
        "schedule",
    ] = Field(...)
    resource_id: UUID4 | None = None
    service_name: str
    metadata: dict[str, any] | None = None
    success: bool = True
