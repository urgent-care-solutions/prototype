from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    is_provider: bool = False
    provider_npi: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = None


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


class UserPermissions(BaseModel):
    user_id: str
    permissions: Dict[str, Any]
