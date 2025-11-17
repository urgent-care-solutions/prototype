from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import redis.asyncio as redis
import logging
from tortoise import Tortoise

from app.config import settings
from app.models import RefreshToken
from app.schemas import TokenResponse, UserInfo, TokenValidationResponse

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def initialize_redis(self):
        try:
            url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
            if settings.REDIS_PASSWORD:
                url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

            self.redis_client = await redis.from_url(
                url, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Token blacklist disabled.")
            self.redis_client = None

    async def close_redis(self):
        if self.redis_client:
            await self.redis_client.aclose()

    def create_access_token(
        self, user_id: str, email: str, role_name: str, org_id: str
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRY_MINUTES
        )
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role_name,
            "org_id": org_id,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRY_DAYS
        )
        to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
        return jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    async def authenticate_user(self, email: str, password: str):
        conn = Tortoise.get_connection("default")

        user_data = await conn.execute_query_dict(
            """
            SELECT u.id, u.email, u.password_hash, u.first_name, u.last_name,
                   u.is_active, u.failed_login_attempts, u.account_locked_until,
                   u.organization_id, r.name as role_name, r.permissions
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.email = $1
            """,
            [email],
        )

        if not user_data:
            return None

        user = user_data[0]

        if not user["is_active"]:
            return None

        if user["account_locked_until"] and user["account_locked_until"] > datetime.now(
            timezone.utc
        ):
            return None

        from passlib.hash import bcrypt

        if not bcrypt.verify(password, user["password_hash"]):
            await conn.execute_query(
                "UPDATE users SET failed_login_attempts = failed_login_attempts + 1, account_locked_until = CASE WHEN failed_login_attempts + 1 >= 5 THEN $1 ELSE NULL END WHERE id = $2",
                [datetime.now(timezone.utc) + timedelta(minutes=30), user["id"]],
            )
            return None

        await conn.execute_query(
            "UPDATE users SET failed_login_attempts = 0, account_locked_until = NULL, last_login = $1 WHERE id = $2",
            [datetime.now(timezone.utc), user["id"]],
        )

        return user

    async def login(self, email: str, password: str) -> Optional[TokenResponse]:
        user = await self.authenticate_user(email, password)

        if not user:
            return None

        access_token = self.create_access_token(
            str(user["id"]),
            user["email"],
            user["role_name"],
            str(user["organization_id"]),
        )
        refresh_token_str = self.create_refresh_token(str(user["id"]))

        await RefreshToken.create(
            user_id=user["id"],
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
        )

        user_info = UserInfo(
            id=str(user["id"]),
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            role_name=user["role_name"],
            organization_id=str(user["organization_id"]),
            permissions=user["permissions"],
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.JWT_EXPIRY_MINUTES * 60,
            user=user_info,
        )

    async def validate_token(self, token: str) -> TokenValidationResponse:
        try:
            if self.redis_client:
                is_blacklisted = await self.redis_client.get(f"blacklist:{token}")
                if is_blacklisted:
                    return TokenValidationResponse(valid=False, message="Token revoked")

            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )

            user_id = payload.get("sub")
            if not user_id:
                return TokenValidationResponse(valid=False, message="Invalid token")

            conn = Tortoise.get_connection("default")
            user_data = await conn.execute_query_dict(
                "SELECT id, email, is_active FROM users WHERE id = $1", [user_id]
            )

            if not user_data or not user_data[0]["is_active"]:
                return TokenValidationResponse(valid=False, message="User inactive")

            return TokenValidationResponse(
                valid=True,
                user_id=user_id,
                email=payload.get("email"),
                role_name=payload.get("role"),
                organization_id=payload.get("org_id"),
                permissions={},
            )

        except JWTError as e:
            logger.error(f"JWT error: {e}")
            return TokenValidationResponse(valid=False, message="Invalid token")
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return TokenValidationResponse(valid=False, message="Validation failed")

    async def logout(self, token: str) -> bool:
        try:
            if not self.redis_client:
                return True

            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            exp = payload.get("exp")

            if exp:
                ttl = exp - int(datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    await self.redis_client.setex(f"blacklist:{token}", ttl, "1")

            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    async def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")

            token_record = await RefreshToken.get_or_none(
                token=refresh_token, is_revoked=False
            )
            if not token_record or token_record.expires_at < datetime.now(timezone.utc):
                return None

            conn = Tortoise.get_connection("default")
            user_data = await conn.execute_query_dict(
                """
                SELECT u.id, u.email, u.first_name, u.last_name, u.is_active,
                       u.organization_id, r.name as role_name, r.permissions
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = $1
                """,
                [user_id],
            )

            if not user_data or not user_data[0]["is_active"]:
                return None

            user = user_data[0]

            access_token = self.create_access_token(
                str(user["id"]),
                user["email"],
                user["role_name"],
                str(user["organization_id"]),
            )

            user_info = UserInfo(
                id=str(user["id"]),
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                role_name=user["role_name"],
                organization_id=str(user["organization_id"]),
                permissions=user["permissions"],
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.JWT_EXPIRY_MINUTES * 60,
                user=user_info,
            )

        except JWTError:
            return None


auth_service = AuthService()
