import logging

from shared.messages import (
    AuditLog,
    UserCreate,
    UserCreated,
    UserDelete,
    UserDeleted,
    UserList,
    UserListed,
    UserPasswordVerified,
    UserPasswordVerify,
    UserRead,
    UserReaded,
    UserUpdate,
    UserUpdated,
)

from src.broker import broker
from src.config import settings
from src.services.user_service import UserService

_log = logging.getLogger(settings.LOGGER)


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
                service_name=settings.SERVICE_NAME,
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
        return UserCreated(
            success=True,
            user_id=user.id,
            email=user.email,
            role_id=user.role_id,
        )


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
                service_name=settings.SERVICE_NAME,
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
        return UserUpdated(
            success=True,
            user_id=user.id,
            email=user.email,
            role_id=user.role_id,
        )


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
                service_name=settings.SERVICE_NAME,
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


@broker.subscriber("user.list")
@broker.publisher("user.listed")
@broker.publisher("audit.log.user")
async def handle_user_list(msg: UserList) -> UserListed:
    try:
        users = (
            await UserService.list_users(
                role_id=msg.role_id, is_active=msg.is_active
            )
            if msg.role_id or msg.is_active is not None
            else await UserService.list_users()
        )
        for user in users:
            await broker.publish(
                AuditLog(
                    user_id=msg.user_id,
                    action="READ",
                    resource_type="user",
                    resource_id=user.id,
                    service_name=settings.SERVICE_NAME,
                    metadata={
                        "action_detail": "listed in user list",
                    },
                ),
                subject="audit.log.user",
            )
        user_list_data = [
            UserReaded(
                user_id=u.id,
                email=u.email,
                role_id=u.role_id,
                success=True,
            )
            for u in users
        ]
    except Exception as e:
        _log.error(f"Error updating user: {e!s}")
        return UserListed(success=False, users=[])
    else:
        _log.info(f"Updated user: {msg.user_id}")
        return UserListed(success=True, users=user_list_data)


@broker.subscriber("user.password.verify")
@broker.publisher("user.password.verified")
@broker.publisher("audit.log.user")
async def handle_user_password_verify(
    msg: UserPasswordVerify,
) -> UserPasswordVerified:
    try:
        user = await UserService.verify_user_password(
            msg.email, msg.password
        )
        await broker.publish(
            AuditLog(
                user_id=msg.user_id,
                action="READ",
                resource_type="user",
                resource_id=user.id,
                service_name=settings.SERVICE_NAME,
                metadata={
                    "action_detail": "password verification",
                },
            ),
            subject="audit.log.user",
        )
    except Exception as e:
        _log.error(f"Error updating user: {e!s}")
        return UserPasswordVerified(success=False)
    else:
        _log.info(f"Updated user: {msg.user_id}")
        return UserPasswordVerified(
            success=True,
            user_id=user.id,
            role_id=user.role_id,
            email=user.email,
            is_active=user.is_active,
        )


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
                service_name=settings.SERVICE_NAME,
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
