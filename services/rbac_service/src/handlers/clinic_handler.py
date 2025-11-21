import logging

from faststream.nats import NatsMessage
from shared.messages import (
    ClinicCreate,
    ClinicCreated,
    ClinicDelete,
    ClinicDeleted,
    ClinicRead,
    ClinicReaded,
    ClinicUpdate,
    ClinicUpdated,
)

from src.broker import broker
from src.config import settings
from src.services.clinic_service import ClinicService

_log = logging.getLogger(settings.LOGGER)


@broker.subscriber("clinic.create")
@broker.publisher("clinic.created")
@broker.publisher("audit.log.clinic")
async def handle_clinic_create(msg: ClinicCreate) -> ClinicCreated:
    _log.info(f"Creating clinic: {msg.name}")
    clinic = await ClinicService.create_clinic(msg)
    return ClinicCreated.model_validate(clinic)


@broker.subscriber("clinic.read")
@broker.publisher("clinic.readed")
@broker.publisher("audit.log.clinic")
async def handle_clinic_read(msg: ClinicRead) -> ClinicReaded:
    _log.info(f"Reading clinic: {msg.clinic_id}")
    # Note: msg.clinic_id comes from ClinicRead in messages.py
    clinic = await ClinicService.get_clinic(msg.clinic_id)
    if not clinic:
        # In a real scenario, you might want to raise a specific error
        # or return a failure message. FastStream handles exceptions well.
        raise ValueError(f"Clinic with id {msg.clinic_id} not found")

    # We construct the response manually or via validation to ensure
    # the 'clinic_id' field required by ClinicReaded is populated
    # from the ORM object's 'id'
    return ClinicReaded.model_validate(clinic, from_attributes=True)


@broker.subscriber("clinic.update")
@broker.publisher("clinic.updated")
@broker.publisher("audit.log.clinic")
async def handle_clinic_update(msg: ClinicUpdate, raw_msg: NatsMessage) -> ClinicUpdated:
    # Assuming the ID is passed either in the message body or we are updating based on context.
    # Since ClinicUpdate in messages.py inherits ClinicBase but doesn't explicitly show an ID,
    # we assume for this implementation that the logic requires an ID.
    # If the ID isn't in the model, we'd typically extract it from metadata or the model itself.

    # NOTE: Based on service signature: update_clinic(clinic_id: UUID, clinic_data: ClinicUpdate)
    # We assume the message contains the target ID.
    # If not present in Pydantic model, this access might fail without schema adjustment.
    clinic_id = getattr(msg, "id", None) or getattr(msg, "clinic_id", None)

    if not clinic_id:
        raise ValueError("Clinic ID is required for update")

    _log.info(f"Updating clinic: {clinic_id}")
    clinic = await ClinicService.update_clinic(clinic_id, msg)
    return ClinicUpdated.model_validate(clinic)


@broker.subscriber("clinic.delete")
@broker.publisher("clinic.deleted")
@broker.publisher("audit.log.clinic")
async def handle_clinic_delete(msg: ClinicDelete) -> ClinicDeleted:
    clinic_id = getattr(msg, "id", None) or getattr(msg, "clinic_id", None)

    if not clinic_id:
        raise ValueError("Clinic ID is required for deletion")

    _log.info(f"Deleting clinic: {clinic_id}")
    clinic = await ClinicService.delete_clinic(clinic_id)
    return ClinicDeleted.model_validate(clinic)
