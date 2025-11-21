import logging
from uuid import uuid4

from shared.messages import DepartmentCreate, DepartmentUpdate
from src.models import Department

_log = logging.getLogger("rich")


# todo: finish implementation
class LocationService:
    @staticmethod
    async def get_location(dep_id: uuid4) -> Department:
        _log.debug(f"Attempting to get location {dep_id}")
        raise NotImplementedError

    @staticmethod
    async def list_locations() -> list[Department]:
        _log.debug("Attempting to list all locations")
        raise NotImplementedError

    @staticmethod
    async def create_location(dep_data: DepartmentCreate) -> Department:
        _log.debug("Attempting to create location")
        raise NotImplementedError

    @staticmethod
    async def update_location(dep_id: uuid4, dep_data: DepartmentUpdate) -> Department:
        _log.debug(f"Attempting to update location {dep_id}")
        raise NotImplementedError

    @staticmethod
    async def delete_location(dep_id: uuid4) -> Department:
        _log.debug(f"Attempting to delete location {dep_id}")
        raise NotImplementedError
