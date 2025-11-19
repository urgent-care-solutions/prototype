from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    organization_id: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class VerifyTokenRequest(BaseModel):
    token: str


class TokenPayload(BaseModel):
    sub: str
    user_id: str
    organization_id: str
    role_id: str
    email: str
    exp: datetime
    type: str
    jti: Optional[str] = None
