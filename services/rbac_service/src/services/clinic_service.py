from uuid import uuid4

from shared.messages import ClinicCreate, ClinicUpdate
from src.models import Clinic


# todo: finish implementation
class ClinicService:
    @staticmethod
    async def get_clinic(clinic_id: uuid4) -> Clinic:
        pass

    @staticmethod
    async def list_clinics() -> list[Clinic]:
        pass

    @staticmethod
    async def create_clinic(clinic_data: ClinicCreate) -> Clinic:
        pass

    @staticmethod
    async def update_clinic(clinic_id: uuid4, clinic_data: ClinicUpdate) -> Clinic:
        pass

    @staticmethod
    async def delete_clinic(clinic_id: uuid4) -> Clinic:
        pass
