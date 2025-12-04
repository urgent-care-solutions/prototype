from typing import Any, Dict, Optional

import strawberry
from fastapi import Request
from strawberry.types import Info

from shared.messages import (
    AuthVerifyRequest,
    AuthVerifyResponse,
    RoleRead,
    RoleReaded,
)
from src.core.nats_client import nats_client


@strawberry.type
class UserContext:
    user_id: str
    email: str
    role_id: str
    permissions: Dict[str, Any]  # e.g. {"patients": ["read", "write"]}


async def get_context(request: Request) -> Dict[str, Any]:
    """
    Builds the GraphQL context.
    1. Extracts Token.
    2. Verifies with Auth Service.
    3. Fetches Permissions from RBAC Service.
    """
    auth_header = request.headers.get("Authorization")
    user_ctx: Optional[UserContext] = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # 1. Verify Token via Auth Service
        try:
            auth_res = await nats_client.request(
                "auth.verify",
                AuthVerifyRequest(token=token),
                AuthVerifyResponse,
            )

            if auth_res.success and auth_res.is_active:
                # 2. Fetch Role Permissions via RBAC Service
                # We need permissions to enforce RBAC at the gateway level
                role_res = await nats_client.request(
                    "role.read",
                    RoleRead(id=auth_res.role_id),
                    RoleReaded,
                )

                permissions = role_res.permissions if role_res.success else {}

                user_ctx = UserContext(
                    user_id=str(auth_res.user_id),
                    email=auth_res.email,
                    role_id=str(auth_res.role_id),
                    permissions=permissions,
                )
        except Exception:
            # Fallback for auth failures (expired token, service down)
            pass

    return {"user": user_ctx, "request": request}


def require_permission(resource: str, action: str):
    """
    Decorator for Resolvers to enforce RBAC.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            info = next((arg for arg in args if isinstance(arg, Info)), None)
            if not info:
                # Handle case where info might be in kwargs
                info = kwargs.get("info")

            if not info or not info.context.get("user"):
                raise Exception("Authentication required")

            user: UserContext = info.context["user"]

            # Check permissions
            # Structure: {"patients": ["read", "write"], ...}
            user_perms = user.permissions.get(resource, [])

            if action not in user_perms:
                raise Exception(
                    f"Access Denied: Missing permission '{action}' on '{resource}'"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
