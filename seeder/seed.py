import asyncio
import logging
import random
import uuid
from datetime import datetime, time
from pathlib import Path

from faker import Faker
from faststream.nats import NatsBroker
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

from shared.messages import (
    AppointmentCreate,
    AppointmentCreated,
    ChargeCreate,
    ClinicCreate,
    ClinicCreated,
    EncounterCreate,
    InsuranceData,
    LocationCreate,
    LocationCreated,
    PatientCreate,
    PatientCreated,
    RoleList,
    RoleListed,
    ScheduleCreate,
    UserCreate,
    UserCreated,
)

# Configuration
THIS_DIR = Path(__file__).parent


class Settings(BaseSettings):
    NATS_CONNECTION_STR: str = "nats://nats:4222"
    SEED_DATA: bool = False

    model_config = SettingsConfigDict(
        env_file=THIS_DIR.parent / ".env",
        env_prefix="PHI__SEEDER__",
        extra="ignore",
    )


settings = Settings()

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger("seeder")

fake = Faker()
broker = NatsBroker(settings.NATS_CONNECTION_STR)


async def wait_for_service(
    subject: str, retries: int = 10, delay: int = 3
):
    """Simple ping to check if a subject has subscribers."""
    logger.info(f"⏳ Waiting for subscribers on {subject}...")
    # FastStream/NatsBroker doesn't expose a clean 'is_subscribed' check easily without internals,
    # so we'll just wait a fixed time for startup, then assume ready for simplicity in this script.
    # In a robust scenario, we might try a health-check request.
    await asyncio.sleep(5)
    logger.info(f"✅ Assuming {subject} is ready.")


async def seed_data():
    if not settings.SEED_DATA:
        logger.warning(
            "🛑 Seeding disabled (SEED_DATA!=true). Exiting."
        )
        return

    logger.info("🌱 Starting Data Seeding via NATS...")

    await broker.connect()

    # 1. Seed Clinic & Location
    await wait_for_service("clinic.create")
    clinic_id = await seed_clinic()
    _ = await seed_location(clinic_id)

    # 2. Fetch Roles (Required for Users)
    roles = await fetch_roles()
    if not roles:
        logger.error(
            "❌ No roles found. Is RBAC service running? Aborting."
        )
        return

    role_map = {r.name: r.id for r in roles}
    logger.info(f"🔑 Found Roles: {list(role_map.keys())}")

    # 3. Seed Providers (Users + Schedules)
    provider_ids = await seed_providers(role_map.get("Physician"))

    # 4. Seed Patients (Users + Patient Records)
    patient_ids = await seed_patients(role_map.get("Patient"))

    # 5. Seed Appointments & Clinical Data
    await seed_appointments(patient_ids, provider_ids)

    logger.info("✅ Seeding Complete!")
    await broker.close()


async def seed_clinic() -> uuid.UUID:
    req = ClinicCreate(
        name="General Hospital",
        address={"city": "New York", "street": "123 Main St"},
        email="contact@hospital.com",
        working_hours={"mon-fri": "08:00-18:00"},
    )
    res: ClinicCreated = await broker.publish(
        req, "clinic.create", rpc=True
    )
    if res.success:
        logger.info(f"🏥 Clinic Created: {res.id}")
        return res.id
    logger.error("Failed to create clinic")
    return uuid.uuid4()


async def seed_location(clinic_id: uuid.UUID) -> uuid.UUID:
    req = LocationCreate(
        clinic_id=clinic_id,
        name="Main Campus",
        type="Hospital",
        address={"city": "New York", "street": "123 Main St"},
    )
    res: LocationCreated = await broker.publish(
        req, "location.create", rpc=True
    )
    if res.success:
        logger.info(f"📍 Location Created: {res.id}")
        return res.id
    return uuid.uuid4()


async def fetch_roles():
    try:
        res: RoleListed = await broker.publish(
            RoleList(), "role.list", rpc=True
        )
        if res.success:
            return res.roles
    except Exception as e:
        logger.error(f"Error fetching roles: {e}")
    return []


async def seed_providers(role_id: uuid.UUID) -> list[uuid.UUID]:
    if not role_id:
        logger.error("⚠️ Physician role not found, skipping providers.")
        return []

    provider_ids = []
    logger.info("👨‍⚕️ Seeding Providers...")

    for _ in range(5):
        # Create User
        u_req = UserCreate(
            role_id=str(role_id),
            email=fake.unique.email(),
            password=fake.password(length=12),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        try:
            u_res: UserCreated = await broker.publish(
                u_req, "user.create", rpc=True
            )
            if u_res.success:
                provider_ids.append(u_res.id)
                # Create Schedule
                for day in range(5):  # Mon-Fri
                    s_req = ScheduleCreate(
                        provider_id=u_res.id,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                    )
                    await broker.publish(
                        s_req, "schedule.create"
                    )  # Fire and forget
        except Exception as e:
            logger.error(f"Failed to create provider: {e}")

    logger.info(f"✅ Created {len(provider_ids)} providers.")
    return provider_ids


async def seed_patients(role_id: uuid.UUID) -> list[uuid.UUID]:
    if not role_id:
        logger.error("⚠️ Patient role not found, skipping patients.")
        return []

    patient_ids = []
    logger.info("users Seeding Patients...")

    for _ in range(20):
        # 1. Create User
        email = fake.unique.email()
        u_req = UserCreate(
            role_id=str(role_id),
            email=email,
            password="password123",  # simple password for testing
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )

        try:
            u_res: UserCreated = await broker.publish(
                u_req, "user.create", rpc=True
            )

            if u_res.success:
                # 2. Create Patient Profile linked to User
                p_req = PatientCreate(
                    user_id=u_res.id,
                    first_name=u_req.first_name,
                    last_name=u_req.last_name,
                    mrn=fake.unique.bothify("MRN-#####"),
                    email=email,
                    insurance=InsuranceData(
                        provider_name="BlueCross",
                        policy_number=fake.bothify("???-#######"),
                    ),
                )
                p_res: PatientCreated = await broker.publish(
                    p_req, "patient.create", rpc=True
                )
                if p_res.success:
                    patient_ids.append(p_res.id)
        except Exception as e:
            logger.error(f"Failed to create patient: {e}")

    logger.info(f"✅ Created {len(patient_ids)} patients.")
    return patient_ids


async def seed_appointments(
    patient_ids: list[uuid.UUID], provider_ids: list[uuid.UUID]
):
    if not patient_ids or not provider_ids:
        return

    logger.info("📅 Seeding Appointments, Encounters & Billing...")

    # 50 Past Appointments (Completed -> Encounter -> Charge)
    # 20 Future Appointments (Scheduled)

    count = 0
    for _ in range(70):
        is_past = _ < 50
        pat_id = random.choice(patient_ids)
        prov_id = random.choice(provider_ids)

        start_date = (
            fake.date_between(start_date="-30d", end_date="-1d")
            if is_past
            else fake.date_between(start_date="+1d", end_date="+30d")
        )
        start_time = datetime.combine(
            start_date, time(random.randint(9, 16), 0)
        )

        # Create Appointment
        req = AppointmentCreate(
            patient_id=pat_id,
            provider_id=prov_id,
            start_time=start_time,
            appointment_type=random.choice(["initial", "follow_up"]),
            reason="Checkup",
        )

        try:
            # We use RPC to get the ID back for linking encounters
            res: AppointmentCreated = await broker.publish(
                req, "appointment.create", rpc=True
            )

            if res.success and is_past:
                # Create Encounter
                enc_req = EncounterCreate(
                    appointment_id=res.id,
                    patient_id=pat_id,
                    provider_id=prov_id,
                    date=start_time,
                    subjective="Patient feels good",
                    objective="BP 120/80",
                    assessment="Healthy",
                    plan="Return in 6 months",
                    diagnosis_codes=[
                        {
                            "code": "Z00.00",
                            "description": "General Exam",
                        }
                    ],
                )
                # Fire and forget / or rpc if strict dependency needed
                await broker.publish(enc_req, "ehr.encounter.create")

                # Create Charge
                bill_req = ChargeCreate(
                    patient_id=pat_id,
                    appointment_id=res.id,
                    amount=150.0,
                    description="Office Visit",
                )
                await broker.publish(bill_req, "billing.charge")
                count += 1
        except Exception as e:
            logger.warning(f"Failed to seed appointment chain: {e}")

    logger.info(
        f"✅ Seeded ~{count} completed appointments chains and ~20 future slots."
    )


if __name__ == "__main__":
    asyncio.run(seed_data())
