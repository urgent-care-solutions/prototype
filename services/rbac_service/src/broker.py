import logging

from faststream import FastStream
from faststream.nats import NatsBroker

from shared.messages import AuditLog, UserCreate, UserCreated, UserUpdate, UserUpdated
from src.services.user_service import UserService

_log = logging.getLogger("rich")
broker = NatsBroker("nats://localhost:4222")

app = FastStream(broker, title="RBAC Service", version="0.1", description="Handles RBAC access to clinic resources")


@broker.subscriber("user.create")
@broker.publisher("user.created")
@broker.publisher("audit.log.user")
async def handle_user_create(msg: UserCreate) -> UserCreated:
    try:
        user = await UserService.create_user(msg)
        await broker.publish(
            AuditLog(
                user_id=msg.user_id,
                action="CREATE",
                resource_type="user",
                resource_id=user.id,
                service_name="rbac-service",
                metadata={
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role_id": user.role_id,
                },
            ),
            subject="audit.log.user",
        )
    except Exception as e:
        _log.error(f"Error creating user: {e!s}")
        return UserCreated(success=False)
    else:
        _log.info(f"Created user: {user.id}")
        return UserCreated(success=True)


@broker.subscriber("user.update")
@broker.publisher("user.updated")
@broker.publisher("audit.log.user")
async def handle_user_update(msg: UserUpdate) -> UserUpdated:
    try:
        user = await UserService.update_user(msg)
        await broker.publish(
            AuditLog(
                user_id=msg.user_id,
                action="UPDATE",
                resource_type="user",
                resource_id=user.id,
                service_name="rbac-service",
                metadata={
                    "updated_fields": 0,  # todo: implement
                },
            ),
            subject="audit.log.user",
        )
    except Exception as e:
        _log.error(f"Error updating user: {e!s}")
        return UserUpdated(success=False)
    else:
        _log.info(f"Updated user: {msg.user_id}")
        return UserUpdated(success=True)


# todo: implement all remaining handlers
