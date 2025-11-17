from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: "UserInfo"


class UserInfo(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role_name: str
    organization_id: str
    permissions: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ValidateTokenRequest(BaseModel):
    token: str


class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role_name: Optional[str] = None
    organization_id: Optional[str] = None
    permissions: Optional[dict] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str
