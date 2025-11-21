import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import UUID4, BaseModel, EmailStr, Field, SecretStr


class BaseMessage(BaseModel):
    message_id: UUID4 = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.now(tz=UTC))
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


class UserPasswordVerify(UserBase):
    password: SecretStr


class UserPasswordVerified(UserPasswordVerify):
    success: bool = True


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
    pass


class ClinicRead(ClinicBase):
    pass


class ClinicReaded(ClinicRead):
    success: bool = True


class ClinicCreate(ClinicBase):
    pass


class ClinicCreated(ClinicCreate):
    success: bool = True


class ClinicUpdate(ClinicBase):
    pass


class ClinicUpdated(ClinicUpdate):
    success: bool = True


class ClinicDelete(ClinicBase):
    pass


class ClinicDeleted(ClinicDelete):
    success: bool = True


class DepartmentBase(BaseMessage):
    pass


class DepartmentRead(DepartmentBase):
    pass


class DepartmentReaded(DepartmentRead):
    success: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentCreated(DepartmentCreate):
    success: bool = True


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentUpdated(DepartmentUpdate):
    success: bool = True


class DepartmentDelete(DepartmentBase):
    pass


class DepartmentDeleted(DepartmentDelete):
    success: bool = True


class AuditLog(BaseMessage):
    action: Literal["CREATE", "READ", "UPDATE", "DELETE"] = Field(...)
    resource_type: Literal["patient", "user", "appointment"] = Field(...)
    resource_id: UUID4 | None = None
    service_name: str
    metadata: dict[str, any] | None = None
    success: bool = True
