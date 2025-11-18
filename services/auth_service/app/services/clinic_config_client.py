import logging
from typing import Optional

import httpx

from app.config import settings
from app.models.user import UserPermissions, UserResponse

logger = logging.getLogger(__name__)


class ClinicConfigClient:
    def __init__(self):
        self.base_url = settings.CLINIC_CONFIG_SERVICE_URL
        self.timeout = 10.0

    async def verify_user_credentials(
        self, email: str, password: str
    ) -> Optional[UserResponse]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users", params={"email": email, "is_active": True}
                )

                if response.status_code != 200:
                    logger.error(f"Failed to fetch user: {response.status_code}")
                    return None

                users = response.json()
                if not users or len(users) == 0:
                    logger.info(f"User not found: {email}")
                    return None

                user_data = users[0]
                user = UserResponse(**user_data)

                verify_response = await client.post(
                    f"{self.base_url}/auth/verify-password",
                    json={"email": email, "password": password},
                )

                if verify_response.status_code != 200:
                    logger.info(f"Invalid password for user: {email}")
                    return None

                return user

            except httpx.RequestError as e:
                logger.error(f"Request error to Clinic Config Service: {e}")
                return None
            except Exception as e:
                logger.error(f"Error verifying user credentials: {e}")
                return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/users/{user_id}")

                if response.status_code != 200:
                    return None

                user_data = response.json()
                return UserResponse(**user_data)

            except Exception as e:
                logger.error(f"Error fetching user by ID: {e}")
                return None

    async def get_user_permissions(self, user_id: str) -> Optional[UserPermissions]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/permissions"
                )

                if response.status_code != 200:
                    return None

                return UserPermissions(**response.json())

            except Exception as e:
                logger.error(f"Error fetching user permissions: {e}")
                return None

                logger.error(f"Error fetching user permissions: {e}")
                return None


clinic_config_client = ClinicConfigClient()
