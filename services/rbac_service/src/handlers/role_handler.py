import logging

from shared.messages import (
    AuditLog,
    RoleCreate,
    RoleCreated,
    RoleDelete,
    RoleDeleted,
    RoleUpdate,
    RoleUpdated,
)

from src.broker import broker
from src.config import settings
from src.services.role_service import RoleService

_log = logging.getLogger(settings.LOGGER)


@broker.subscriber("role.create")
@broker.publisher("role.created")
@broker.publisher("audit.log.role")
async def handle_role_create(msg: RoleCreate) -> RoleCreated:
    _log.debug(f"Handling role creation for role: {msg.role_name}")
    try:
        role = await RoleService.create_role(msg)
        await broker.publish(
            AuditLog(
                user_id=msg.id,
                action="CREATE",
                resource_type="role",
                resource_id=role.id,
                service_name=settings.SERVICE_NAME,
                metadata={
                    "role_name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                },
            ),
            subject="audit.log.role",
        )
    except Exception as e:
        _log.error(f"Error creating role: {e!s}")
        return RoleCreated(success=False)
    else:
        _log.info(f"Created role: {role.id}")
        return RoleCreated(success=True)


@broker.subscriber("role.update")
@broker.publisher("role.updated")
@broker.publisher("audit.log.role")
async def handle_role_update(msg: RoleUpdate) -> RoleUpdated:
    _log.debug(f"Handling role update for role: {msg.role_name}")
    try:
        role = await RoleService.update_role(msg.id, msg)
        await broker.publish(
            AuditLog(
                user_id=msg.id,
                action="UPDATE",
                resource_type="role",
                resource_id=role.id,
                service_name=settings.SERVICE_NAME,
                metadata={
                    "role_name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                },
            ),
            subject="audit.log.role",
        )
    except Exception as e:
        _log.error(f"Error updating role: {e!s}")
        return RoleUpdated(success=False)
    else:
        _log.info(f"Updated role: {role.id}")
        return RoleUpdated(success=True)


@broker.subscriber("role.delete")
@broker.publisher("role.deleted")
@broker.publisher("audit.log.role")
async def handle_role_delete(msg: RoleDelete) -> RoleDeleted:
    _log.debug(f"Handling role update for role: {msg.role_name}")
    try:
        role = await RoleService.delete_role(msg.id)
        await broker.publish(
            AuditLog(
                user_id=msg.id,
                action="DELETE",
                resource_type="role",
                resource_id=role.id,
                service_name=settings.SERVICE_NAME,
                metadata={
                    "role_name": role.name,
                    "description": role.description,
                    "permissions": role.permissions,
                },
            ),
            subject="audit.log.role",
        )
    except Exception as e:
        _log.error(f"Error updating role: {e!s}")
        return RoleDeleted(success=False)
    else:
        _log.info(f"Updated role: {role.id}")
        return RoleDeleted(success=True)
