import logging

from shared.messages import (
    DepartmentCreate,
    DepartmentCreated,
    DepartmentDelete,
    DepartmentDeleted,
    DepartmentRead,
    DepartmentReaded,
    DepartmentUpdate,
    DepartmentUpdated,
)

from src.broker import broker
from src.config import settings
from src.services.department_service import DepartmentService

_log = logging.getLogger(settings.LOGGER)


@broker.subscriber("department.create")
@broker.publisher("department.created")
@broker.publisher("audit.log.department")
async def handle_department_create(
    msg: DepartmentCreate,
) -> DepartmentCreated:
    _log.info(
        f"Creating department of type {msg.type} for location {msg.location_id}"
    )
    dep = await DepartmentService.create_department(msg)
    return DepartmentCreated.model_validate(dep)


@broker.subscriber("department.read")
@broker.publisher("department.readed")
@broker.publisher("audit.log.department")
async def handle_department_read(
    msg: DepartmentRead,
) -> DepartmentReaded:
    _log.info(f"Reading department: {msg.department_id}")
    dep = await DepartmentService.get_department(msg.department_id)
    if not dep:
        raise ValueError(
            f"Department with id {msg.department_id} not found"
        )

    # Mapping ORM 'id' to message 'department_id' usually handled by alias
    # or manual construction if auto-validation fails.
    response = DepartmentReaded.model_validate(
        dep, from_attributes=True
    )
    # Ensure ID is set if names differ (id vs department_id)
    if not response.department_id and hasattr(dep, "id"):
        response.department_id = dep.id
    return response


@broker.subscriber("department.update")
@broker.publisher("department.updated")
@broker.publisher("audit.log.department")
async def handle_department_update(
    msg: DepartmentUpdate,
) -> DepartmentUpdated:
    # Service signature: update_department(dep_id: UUID, dep_data: DepartmentUpdate)
    # Using getattr to handle potential naming differences in shared messages
    dep_id = getattr(msg, "id", None) or getattr(
        msg, "department_id", None
    )

    if not dep_id:
        raise ValueError("Department ID is required for update")

    _log.info(f"Updating department: {dep_id}")
    dep = await DepartmentService.update_department(dep_id, msg)
    return DepartmentUpdated.model_validate(dep)


@broker.subscriber("department.delete")
@broker.publisher("department.deleted")
@broker.publisher("audit.log.department")
async def handle_department_delete(
    msg: DepartmentDelete,
) -> DepartmentDeleted:
    dep_id = getattr(msg, "id", None) or getattr(
        msg, "department_id", None
    )

    if not dep_id:
        raise ValueError("Department ID is required for deletion")

    _log.info(f"Deleting department: {dep_id}")
    dep = await DepartmentService.delete_department(dep_id)
    return DepartmentDeleted.model_validate(dep)
