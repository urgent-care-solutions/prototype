import logging
from uuid import uuid4

from shared.messages import ClinicCreate, ClinicUpdate

from src.config import settings
from src.models import Clinic

_log = logging.getLogger(settings.LOGGER)


# todo: finish implementation
class ClinicService:
    @staticmethod
    async def get_clinic(clinic_id: uuid4) -> Clinic:
        _log.debug(f"Attempting to get clinic {clinic_id}")
        raise NotImplementedError

    @staticmethod
    async def list_clinics() -> list[Clinic]:
        _log.debug("Attempting to list all clinics")
        raise NotImplementedError

    @staticmethod
    async def create_clinic(clinic_data: ClinicCreate) -> Clinic:
        _log.debug("Attempting to create clinic")
        raise NotImplementedError

    @staticmethod
    async def update_clinic(
        clinic_id: uuid4, clinic_data: ClinicUpdate
    ) -> Clinic:
        _log.debug(f"Attempting to update clinic {clinic_id}")
        raise NotImplementedError

    @staticmethod
    async def delete_clinic(clinic_id: uuid4) -> Clinic:
        _log.debug(f"Attempting to delete clinic {clinic_id}")
        raise NotImplementedError
