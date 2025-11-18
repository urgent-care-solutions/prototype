from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    organization_id: UUID
    role_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_provider: bool
    provider_npi: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPermissions(BaseModel):
    user_id: str
    permissions: Dict[str, Any]
