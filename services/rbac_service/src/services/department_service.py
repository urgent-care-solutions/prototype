import logging
from uuid import uuid4

from shared.messages import DepartmentCreate, DepartmentUpdate
from src.models import Department

_log = logging.getLogger("rich")


class DepartmentService:
    @staticmethod
    async def get_department(dep_id: uuid4) -> Department:
        _log.debug(f"Attempting to get department {dep_id}")
        pass

    @staticmethod
    async def list_departments() -> list[Department]:
        _log.debug("Attempting to list all departments")
        pass

    @staticmethod
    async def create_department(dep_data: DepartmentCreate) -> Department:
        _log.debug("Attempting to create department")
        pass

    @staticmethod
    async def update_department(dep_id: uuid4, dep_data: DepartmentUpdate) -> Department:
        _log.debug(f"Attempting to update department {dep_id}")
        pass

    @staticmethod
    async def delete_department(dep_id: uuid4) -> Department:
        _log.debug(f"Attempting to delete department {dep_id}")
        pass
