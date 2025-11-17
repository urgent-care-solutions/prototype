from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from app.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ValidateTokenRequest,
    TokenValidationResponse,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/auth/login", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def login(request: LoginRequest):
    result = await auth_service.login(request.email, request.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or account locked",
        )

    return result


@router.post("/auth/logout", status_code=status.HTTP_200_OK)
async def logout(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No authorization token"
        )

    token = authorization.split(" ")[1]
    success = await auth_service.logout(token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )

    return {"message": "Logged out successfully"}


@router.post(
    "/auth/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def refresh_token(request: RefreshTokenRequest):
    result = await auth_service.refresh_access_token(request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return result


@router.post(
    "/auth/validate",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_token(request: ValidateTokenRequest):
    result = await auth_service.validate_token(request.token)
    return result
