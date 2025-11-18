from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.user import UserResponse


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, mock_user_response):
    with patch(
        "app.services.clinic_config_client.clinic_config_client.verify_user_credentials"
    ) as mock_verify:
        mock_verify.return_value = UserResponse(**mock_user_response)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Test@Password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    with patch(
        "app.services.clinic_config_client.clinic_config_client.verify_user_credentials"
    ) as mock_verify:
        mock_verify.return_value = None

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, mock_user_response):
    with (
        patch(
            "app.services.clinic_config_client.clinic_config_client.verify_user_credentials"
        ) as mock_verify,
        patch(
            "app.services.clinic_config_client.clinic_config_client.get_user_by_id"
        ) as mock_get_user,
        patch("app.core.redis.redis_client.get_refresh_token") as mock_redis_get,
        patch("app.core.redis.redis_client.set_refresh_token") as mock_redis_set,
        patch("app.core.redis.redis_client.delete_refresh_token") as mock_redis_del,
        patch("app.core.redis.redis_client.is_token_blacklisted") as mock_blacklist,
    ):
        mock_verify.return_value = UserResponse(**mock_user_response)
        mock_get_user.return_value = UserResponse(**mock_user_response)
        mock_redis_get.return_value = mock_user_response["id"]
        mock_blacklist.return_value = False

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Test@Password123"},
        )

        refresh_token = login_response.json()["refresh_token"]

        refresh_response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, mock_user_response):
    with (
        patch(
            "app.services.clinic_config_client.clinic_config_client.verify_user_credentials"
        ) as mock_verify,
        patch("app.core.redis.redis_client.blacklist_token") as mock_blacklist,
        patch("app.core.redis.redis_client.delete_refresh_token") as mock_delete,
    ):
        mock_verify.return_value = UserResponse(**mock_user_response)

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Test@Password123"},
        )

        tokens = login_response.json()

        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

        assert logout_response.status_code == 204


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

    data = response.json()
    assert "status" in data

    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data
