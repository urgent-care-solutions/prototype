import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_clinic(client: AsyncClient):
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": "Test Clinic Org", "timezone": "America/New_York"},
    )
    org_data = org_response.json()
    org_id = org_data["id"]

    clinic_data = {
        "name": "Test Clinic",
        "organization_id": org_id,
        "phone": "555-0100",
        "timezone": "America/New_York",
        "working_hours": {"monday": {"open": "08:00", "close": "17:00"}},
    }

    response = await client.post("/api/v1/clinics", json=clinic_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Clinic"
    assert data["phone"] == "555-0100"


@pytest.mark.asyncio
async def test_list_clinics(client: AsyncClient):
    response = await client.get("/api/v1/clinics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_clinic_hours(client: AsyncClient):
    org_response = await client.post(
        "/api/v1/organizations", json={"name": "Test Clinic Hours Org"}
    )
    org_id = org_response.json()["id"]

    clinic_response = await client.post(
        "/api/v1/clinics",
        json={
            "name": "Test Clinic Hours",
            "organization_id": org_id,
            "working_hours": {"monday": {"open": "09:00", "close": "18:00"}},
        },
    )
    clinic_id = clinic_response.json()["id"]

    response = await client.get(f"/api/v1/clinics/{clinic_id}/hours")
    assert response.status_code == 200
    data = response.json()
    assert "working_hours" in data
