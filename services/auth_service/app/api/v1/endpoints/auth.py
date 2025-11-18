from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    VerifyTokenRequest,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    return await auth_service.login(request.email, request.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    return await auth_service.refresh(request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: LogoutRequest, authorization: Optional[str] = Header(None)):
    access_token = None
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token required in Authorization header",
        )

    await auth_service.logout(access_token, request.refresh_token)
    return None


@router.post("/verify")
async def verify_token(request: VerifyTokenRequest):
    payload = await auth_service.verify(request.token)
    return {"valid": True, "payload": payload}
