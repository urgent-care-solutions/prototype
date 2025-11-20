import uuid
from datetime import UTC, datetime

from pydantic import UUID4, BaseModel, EmailStr, Field


class BaseMessage(BaseModel):
    message_id: UUID4 = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.now(tz=UTC))
    user_id: UUID4 | None = None
    request_id: UUID4 | None = None


class BaseRole(BaseMessage):
    pass


class RoleCreate(BaseRole):
    pass


class RoleUpdate(BaseRole):
    pass


class RoleDelete(BaseRole):
    pass


class UserBase(BaseMessage):
    role_id: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserCreated(UserBase):
    success: bool = True


class UserUpdate(UserBase):
    pass


class UserDelete(UserBase):
    pass


class ClinicBase(BaseMessage):
    pass


class ClinicCreate(ClinicBase):
    pass


class ClinicUpdate(ClinicBase):
    pass


class ClinicDelete(ClinicBase):
    pass


class AuditLog(BaseMessage):
    action: str = Field(..., description="CREATE|READ|UPDATE|DELETE")
    resource_type: str = Field(..., description="patient|appointment|etc")
    resource_id: UUID4 | None = None
    service_name: str
    metadata: dict[str, any] | None = None
    success: bool = True
