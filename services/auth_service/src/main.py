import asyncio
import logging
from contextlib import asynccontextmanager

from faststream import FastStream
from faststream.asgi import AsgiFastStream, make_ping_asgi
from faststream.nats import NatsBroker
from shared.messages import (
    AuditLog,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthLogoutRequest,
    AuthLogoutResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
    UserPasswordVerified,
    UserPasswordVerify,
)

from src.config import settings
from src.session_manager import SessionManager

# Setup Logging
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[logging.StreamHandler()],
)
_log = logging.getLogger(settings.LOGGER)

# Setup Broker and Session Manager
broker = NatsBroker(settings.NATS_CONNECTION_STR)
session_manager = SessionManager()


@asynccontextmanager
async def lifespan(app):
    _log.info(f"Starting {settings.SERVICE_NAME}...")
    await broker.connect()
    yield
    await session_manager.close()
    await broker.close()
    _log.info(f"{settings.SERVICE_NAME} stopped.")


app = AsgiFastStream(
    FastStream(
        broker,
        title=settings.SERVICE_NAME,
        version=settings.VERSION,
        description=settings.SERVICE_DESCRIPTION,
        lifespan=lifespan,
    ),
    asgi_routes=[
        (
            "/healthz",
            make_ping_asgi(
                broker, timeout=1.0, include_in_schema=False
            ),
        )
    ],
)


@broker.subscriber("auth.login")
@broker.publisher("auth.login.response")
@broker.publisher("audit.log.auth")
async def handle_login(msg: AuthLoginRequest) -> AuthLoginResponse:
    _log.info(f"Login attempt for: {msg.email}")

    # 1. Verify credentials via RBAC Service (RPC call)
    try:
        rbac_response: UserPasswordVerified = await broker.publish(
            UserPasswordVerify(email=msg.email, password=msg.password),
            subject="user.password.verify",
            rpc=True,
            timeout=5.0,  # Wait max 5 seconds for RBAC
        )
    except TimeoutError:
        _log.error("RBAC service timeout during login")
        return AuthLoginResponse(
            success=False, error="Authentication service timeout"
        )
    except Exception as e:
        _log.error(f"Error communicating with RBAC: {e}")
        return AuthLoginResponse(
            success=False, error="Internal login error"
        )

    # 2. Check verification result
    if not rbac_response.success or not rbac_response.is_active:
        _log.warning(
            f"Failed login for {msg.email}: Invalid credentials or inactive account"
        )

        # Log audit failure
        await broker.publish(
            AuditLog(
                action="READ",
                resource_type="user",
                service_name=settings.SERVICE_NAME,
                metadata={"event": "login_failed", "email": msg.email},
            ),
            "audit.log.auth",
        )
        return AuthLoginResponse(
            success=False, error="Invalid credentials"
        )

    # 3. Create Session
    token = await session_manager.create_session(rbac_response)

    # 4. Log Success
    await broker.publish(
        AuditLog(
            action="READ",
            resource_type="user",
            resource_id=rbac_response.user_id,
            service_name=settings.SERVICE_NAME,
            metadata={"event": "login_success"},
        ),
        "audit.log.auth",
    )

    return AuthLoginResponse(
        success=True,
        token=token,
        user_id=rbac_response.user_id,
        role_id=rbac_response.role_id,
    )


@broker.subscriber("auth.verify")
@broker.publisher("auth.verify.response")
@broker.publisher("audit.log.auth")
async def handle_verify(msg: AuthVerifyRequest) -> AuthVerifyResponse:
    session_data = await session_manager.get_session(msg.token)

    if not session_data:
        await broker.publish(
            AuditLog(
                action="READ",
                resource_type="user",
                resource_id=msg.token,
                service_name=settings.SERVICE_NAME,
                metadata={"event": "auth_verify", "success": False},
            ),
            "audit.log.auth",
        )
        return AuthVerifyResponse(success=False)

    await broker.publish(
        AuditLog(
            action="READ",
            resource_type="user",
            resource_id=msg.token,
            service_name=settings.SERVICE_NAME,
            metadata={"event": "auth_verify", "success": True},
        ),
        "audit.log.auth",
    )
    return AuthVerifyResponse(
        success=True,
        user_id=session_data["user_id"],
        role_id=session_data["role_id"],
        email=session_data["email"],
        is_active=session_data["is_active"],
    )


@broker.subscriber("auth.logout")
@broker.publisher("auth.logout.response")
@broker.publisher("audit.log.auth")
async def handle_logout(msg: AuthLogoutRequest) -> AuthLogoutResponse:
    success = await session_manager.delete_session(msg.token)
    await broker.publish(
        AuditLog(
            action="READ",
            resource_type="user",
            resource_id=msg.token,
            service_name=settings.SERVICE_NAME,
            metadata={"event": "logout", "success": success},
        ),
        "audit.log.auth",
    )
    return AuthLogoutResponse(success=success)


if __name__ == "__main__":
    asyncio.run(app.run())
