import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": "Test Role Org", "timezone": "America/New_York"},
    )
    org_data = org_response.json()
    org_id = org_data["id"]

    role_data = {
        "name": "Custom Role",
        "description": "Custom test role",
        "permissions": {"test": ["read", "write"]},
        "organization_id": org_id,
    }

    response = await client.post("/api/v1/roles", json=role_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Custom Role"
    assert data["permissions"] == {"test": ["read", "write"]}


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient):
    response = await client.get("/api/v1/roles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_initialize_default_roles(client: AsyncClient):
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": "Test Default Roles Org", "timezone": "America/New_York"},
    )
    org_data = org_response.json()
    org_id = org_data["id"]

    response = await client.get(f"/api/v1/roles?organization_id={org_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    role_names = [role["name"] for role in data]
    assert "Admin" in role_names
    assert "Physician" in role_names
    assert "Nurse" in role_names
