import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": "Test User Org", "timezone": "America/New_York"},
    )
    org_data = org_response.json()
    org_id = org_data["id"]

    roles_response = await client.get(f"/api/v1/roles?organization_id={org_id}")
    roles_data = roles_response.json()
    role_id = roles_data[0]["id"]

    user_data = {
        "email": "testuser@example.com",
        "password": "TestPass@123",
        "first_name": "Test",
        "last_name": "User",
        "organization_id": org_id,
        "role_id": role_id,
    }

    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["first_name"] == "Test"
    assert "password" not in data


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
