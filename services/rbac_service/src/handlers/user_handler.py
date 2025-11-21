import logging

from shared.messages import (
    AuditLog,
    UserCreate,
    UserCreated,
    UserDelete,
    UserDeleted,
    UserRead,
    UserReaded,
    UserUpdate,
    UserUpdated,
)
from src import broker
from src.services.user_service import UserService

_log = logging.getLogger("rich")


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
@broker.subscriber("user.read")
@broker.publisher("user.readed")
@broker.publisher("audit.log.user")
async def handle_user_get(msg: UserRead) -> UserReaded:
    try:
        user = (
            await UserService.get_user_by_id(msg.user_id)
            if msg.user_id
            else await UserService.get_user_by_email(msg.email)
        )
        await broker.publish(
            AuditLog(
                user_id=msg.user_id,
                action="READ",
                resource_type="user",
                resource_id=user.id,
                service_name="rbac-service",
                metadata={},
            ),
            subject="audit.log.user",
        )
    except Exception as e:
        _log.error(f"Error updating user: {e!s}")
        return UserReaded(success=False)
    else:
        _log.info(f"Updated user: {msg.user_id}")
        return UserReaded(success=True)


@broker.subscriber("user.delete")
@broker.publisher("user.deleted")
@broker.publisher("audit.log.user")
async def handle_user_delete(msg: UserDelete) -> UserDeleted:
    try:
        user = await UserService.delete_user(msg.user_id)
        await broker.publish(
            AuditLog(
                user_id=msg.user_id,
                action="DELETE",
                resource_type="user",
                resource_id=user.id,
                service_name="rbac-service",
                metadata={},
            ),
            subject="audit.log.user",
        )
    except Exception as e:
        _log.error(f"Error updating user: {e!s}")
        return UserDeleted(success=False)
    else:
        _log.info(f"Updated user: {msg.user_id}")
        return UserDeleted(success=True)
