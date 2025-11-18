import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status

from app.config import settings
from app.core.redis import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)
from app.services.clinic_config_client import clinic_config_client

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    async def login(email: str, password: str) -> TokenResponse:
        user = await clinic_config_client.verify_user_credentials(email, password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
            )

        token_data = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "organization_id": str(user.organization_id),
            "role_id": str(user.role_id),
            "email": user.email,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        refresh_payload = decode_token(refresh_token)
        if refresh_payload and "jti" in refresh_payload:
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            redis_client.set_refresh_token(refresh_payload["jti"], str(user.id), ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            organization_id=str(user.organization_id),
        )

    @staticmethod
    async def refresh(refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token",
            )

        if redis_client.is_token_blacklisted(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        jti = payload.get("jti")
        if jti:
            stored_user_id = redis_client.get_refresh_token(jti)
            if not stored_user_id or stored_user_id != payload.get("user_id"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

        user_id = payload.get("user_id")
        user = await clinic_config_client.get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        token_data = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "organization_id": str(user.organization_id),
            "role_id": str(user.role_id),
            "email": user.email,
        }

        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        if jti:
            redis_client.delete_refresh_token(jti)

        new_payload = decode_token(new_refresh_token)
        if new_payload and "jti" in new_payload:
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            redis_client.set_refresh_token(new_payload["jti"], str(user.id), ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            organization_id=str(user.organization_id),
        )

    @staticmethod
    async def logout(access_token: str, refresh_token: Optional[str] = None):
        access_payload = decode_token(access_token)
        if access_payload:
            exp = access_payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                ttl = int((exp_datetime - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    redis_client.blacklist_token(access_token, ttl)

        if refresh_token:
            refresh_payload = decode_token(refresh_token)
            if refresh_payload:
                jti = refresh_payload.get("jti")
                if jti:
                    redis_client.delete_refresh_token(jti)

                exp = refresh_payload.get("exp")
                if exp:
                    exp_datetime = datetime.fromtimestamp(exp)
                    ttl = int((exp_datetime - datetime.utcnow()).total_seconds())
                    if ttl > 0:
                        redis_client.blacklist_token(refresh_token, ttl)

    @staticmethod
    async def verify(token: str) -> dict:
        if redis_client.is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        payload = verify_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        return payload

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        return payload


auth_service = AuthService()
