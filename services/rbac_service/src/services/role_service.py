from uuid import uuid4

from shared.messages import RoleCreate, RoleUpdate
from src.models import Role


class RoleService:
    @staticmethod
    async def create_role(role_data: RoleCreate) -> Role:
        pass

    @staticmethod
    async def get_role(role_id: uuid4) -> Role:
        pass

    @staticmethod
    async def list_roles(*, is_active: bool | None = None) -> list[Role]:
        pass

    @staticmethod
    async def update_role(role_id: uuid4, role_data: RoleUpdate) -> Role:
        pass

    @staticmethod
    async def delete_role(role_id: uuid4) -> Role:
        pass

    @staticmethod
    async def initialize_default_roles() -> list[Role]:
        default_roles = [
            {
                "name": "Admin",
                "description": "Full system configuration and user management",
                "permissions": {
                    "patients": ["read", "write", "delete"],
                    "appointments": ["read", "write", "delete"],
                    "billing": ["read", "write", "delete"],
                    "reports": ["read", "export"],
                    "users": ["read", "write", "delete"],
                    "settings": ["read", "write"],
                },
            },
            {
                "name": "Physician",
                "description": "Full EHR access and patient management",
                "permissions": {
                    "patients": ["read", "write"],
                    "appointments": ["read", "write"],
                    "ehr": ["read", "write"],
                    "prescriptions": ["read", "write"],
                    "billing": ["read"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Nurse",
                "description": "Vital signs and rooming access",
                "permissions": {
                    "patients": ["read"],
                    "appointments": ["read"],
                    "ehr": ["read", "write_vitals"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Front Desk",
                "description": "Scheduling and patient registration",
                "permissions": {
                    "patients": ["read", "write_demographics"],
                    "appointments": ["read", "write"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Biller",
                "description": "Claims management and billing",
                "permissions": {
                    "patients": ["read"],
                    "billing": ["read", "write"],
                    "claims": ["read", "write"],
                    "reports": ["read"],
                },
            },
            {
                "name": "Accountant",
                "description": "Financial data and payments",
                "permissions": {
                    "billing": ["read"],
                    "payments": ["read", "write"],
                    "reports": ["read", "export"],
                },
            },
        ]
        pass
