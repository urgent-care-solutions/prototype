import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_organization(client: AsyncClient):
    response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Test Clinic",
            "timezone": "America/New_York",
            "subscription_tier": "standard",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Clinic"
    assert data["timezone"] == "America/New_York"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_organizations(client: AsyncClient):
    response = await client.get("/api/v1/organizations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_organization_not_found(client: AsyncClient):
    response = await client.get(
        "/api/v1/organizations/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
