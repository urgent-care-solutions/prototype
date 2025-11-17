import asyncio
import sys
from uuid import uuid4
from app.db.database import init_db, close_db
from app.models import Organization, Role, User, Clinic


async def seed_mock_data():
    await init_db()
    print("Database initialized")

    org = await Organization.create(
        id=uuid4(),
        name="Demo Clinic Organization",
        type="Healthcare",
        timezone="America/New_York",
        settings={"max_users": 50, "features": ["ehr", "billing", "scheduling"]},
    )
    print(f"Created organization: {org.name}")

    roles_data = [
        {
            "name": "Admin",
            "description": "Full system access",
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
            "description": "Clinical access",
            "permissions": {
                "patients": ["read", "write"],
                "appointments": ["read", "write"],
                "ehr": ["read", "write"],
                "prescriptions": ["read", "write"],
            },
        },
        {
            "name": "Nurse",
            "description": "Nursing access",
            "permissions": {
                "patients": ["read"],
                "appointments": ["read"],
                "ehr": ["read", "write_vitals"],
            },
        },
        {
            "name": "Front Desk",
            "description": "Front desk access",
            "permissions": {
                "patients": ["read", "write_demographics"],
                "appointments": ["read", "write"],
            },
        },
    ]

    roles = []
    for role_data in roles_data:
        role = await Role.create(
            id=uuid4(),
            organization_id=org.id,
            name=role_data["name"],
            description=role_data["description"],
            permissions=role_data["permissions"],
            is_system_role=True,
        )
        roles.append(role)
        print(f"Created role: {role.name}")

    admin_role = next(r for r in roles if r.name == "Admin")
    physician_role = next(r for r in roles if r.name == "Physician")

    admin_user = await User.create(
        id=uuid4(),
        organization_id=org.id,
        role_id=admin_role.id,
        email="admin@demo.clinic",
        password_hash=User.hash_password("adm"),
        first_name="System",
        last_name="Administrator",
        is_provider=False,
    )
    print(f"Created admin user: {admin_user.email}")

    physician_user = await User.create(
        id=uuid4(),
        organization_id=org.id,
        role_id=physician_role.id,
        email="doctor@demo.clinic",
        password_hash=User.hash_password("doc"),
        first_name="John",
        last_name="Smith",
        is_provider=True,
        provider_npi="1234567890",
    )
    print(f"Created physician user: {physician_user.email}")

    clinic = await Clinic.create(
        id=uuid4(),
        organization_id=org.id,
        name="Demo Main Clinic",
        address={
            "street": "123 Medical Plaza",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
        },
        phone="555-0100",
        email="info@demo.clinic",
        working_hours={
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "17:00"},
            "friday": {"open": "08:00", "close": "15:00"},
            "saturday": {"closed": True},
            "sunday": {"closed": True},
        },
    )
    print(f"Created clinic: {clinic.name}")

    print("\nMock data seeding completed successfully!")
    print(f"Organization ID: {org.id}")
    print(f"Admin email: {admin_user.email} | Password: Admin@123456")
    print(f"Physician email: {physician_user.email} | Password: Doctor@123456")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_mock_data())
