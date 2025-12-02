import logging

from shared.messages import (
    LocationCreate,
    LocationCreated,
    LocationDelete,
    LocationDeleted,
    LocationRead,
    LocationReaded,
    LocationUpdate,
    LocationUpdated,
)

from src.broker import broker
from src.config import settings
from src.services.location_service import LocationService

_log = logging.getLogger(settings.LOGGER)


@broker.subscriber("location.create")
@broker.publisher("location.created")
@broker.publisher("audit.log.location")
async def handle_location_create(
    msg: LocationCreate,
) -> LocationCreated:
    _log.info(f"Creating location for clinic: {msg.clinic_id}")
    loc = await LocationService.create_location(msg)
    return LocationCreated.model_validate(loc)


@broker.subscriber("location.read")
@broker.publisher("location.readed")
@broker.publisher("audit.log.location")
async def handle_location_read(msg: LocationRead) -> LocationReaded:
    # LocationRead has 'id' or 'location_id' depending on exact definition,
    # assuming 'id' based on other messages or standard patterns.
    loc_id = getattr(msg, "id", None) or getattr(
        msg, "location_id", None
    )

    if not loc_id:
        # Fallback: check if message has only one UUID field
        raise ValueError("Location ID required for read")

    _log.info(f"Reading location: {loc_id}")
    loc = await LocationService.get_location(loc_id)
    if not loc:
        raise ValueError(f"Location {loc_id} not found")

    return LocationReaded.model_validate(loc)


@broker.subscriber("location.update")
@broker.publisher("location.updated")
@broker.publisher("audit.log.location")
async def handle_location_update(
    msg: LocationUpdate,
) -> LocationUpdated:
    # LocationUpdate explicitly has 'id: UUID4' in messages.py
    _log.info(f"Updating location: {msg.id}")
    loc = await LocationService.update_location(msg.id, msg)
    return LocationUpdated.model_validate(loc)


@broker.subscriber("location.delete")
@broker.publisher("location.deleted")
@broker.publisher("audit.log.location")
async def handle_location_delete(
    msg: LocationDelete,
) -> LocationDeleted:
    # LocationDelete is a BaseMessage, assumes ID is available
    loc_id = getattr(msg, "id", None) or getattr(
        msg, "location_id", None
    )

    if not loc_id:
        raise ValueError("Location ID required for delete")

    _log.info(f"Deleting location: {loc_id}")
    loc = await LocationService.delete_location(loc_id)
    return LocationDeleted.model_validate(loc)
