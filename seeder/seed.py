import asyncio
import logging
import os
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

# Add project root to path so we can import models
sys.path.append("/app")

from faker import Faker
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Configuration ---
SEED_ENABLED = os.getenv("SEED_DATA", "false").lower() == "true"
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seeder")

fake = Faker()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Docker Volume Mount Paths
DB_PATHS = {
    "rbac": Path("/data/rbac/rbac.db"),
    "patient": Path("/data/patients/patients.db"),
    "appointments": Path("/data/appointments/appointments.db"),
    "ehr": Path("/data/ehr/ehr.db"),
    "billing": Path("/data/billing/integration.db"),
    "notification": Path("/data/notification/notification.db"),
    "reporting": Path("/data/reporting/reporting.db"),
    "audit": Path("/data/audit/audit.db"),
}

# --- Import Models ---
# We assume the /app directory contains the full repo structure
try:
    from services.appointments_service.src.models import (
        Appointment,
        ProviderSchedule,
    )
    from services.appointments_service.src.models import (
        Base as ApptBase,
    )
    from services.audit_service.src.models import Base as AuditBase
    from services.ehr_service.src.models import Base as EhrBase
    from services.ehr_service.src.models import (
        Encounter,
        Prescription,
        Vitals,
    )
    from services.integration_service.src.models import (
        Base as BillingBase,
    )
    from services.integration_service.src.models import Transaction
    from services.notification_service.src.models import (
        Base as NotifBase,
    )
    from services.patient_service.src.models import Base as PatientBase
    from services.patient_service.src.models import Patient
    from services.rbac_service.src.models import Base as RbacBase
    from services.rbac_service.src.models import (
        Clinic,
        Department,
        Location,
        Role,
        User,
    )
    from services.reporting_service.src.models import Base as ReportBase
    from services.reporting_service.src.models import (
        ReportingAppointment,
        ReportingPatient,
        ReportingTransaction,
    )
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    sys.exit(1)


class DBConnection:
    def __init__(self, name, base_model):
        self.name = name
        self.path = DB_PATHS[name]
        self.url = f"sqlite+aiosqlite:///{self.path}"
        self.base = base_model
        self.engine = create_async_engine(self.url, echo=False)
        self.Session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        # We DO NOT drop tables here. We assume Alembic in the services
        # has already created the schema. We just clear the data.
        async with self.engine.begin() as conn:
            for table in reversed(self.base.metadata.sorted_tables):
                await conn.execute(table.delete())

    async def close(self):
        await self.engine.dispose()


async def wait_for_dbs():
    """Wait until all DB files exist (created by service migrations)."""
    logger.info(
        "⏳ Waiting for database files to be created by services..."
    )
    while True:
        all_exist = True
        for name, path in DB_PATHS.items():
            if not path.exists():
                logger.info(f"Waiting for {name} DB at {path}...")
                all_exist = False

        if all_exist:
            logger.info("✅ All databases found.")
            break
        await asyncio.sleep(2)


async def seed_data():
    if not SEED_ENABLED:
        logger.info(
            "🛑 Seeding disabled (SEED_DATA!=true). Sleeping..."
        )
        # Keep container alive briefly then exit, or just exit.
        return

    await wait_for_dbs()

    logger.info("🌱 Starting Database Seed...")

    dbs = {
        "rbac": DBConnection("rbac", RbacBase),
        "patient": DBConnection("patient", PatientBase),
        "appointments": DBConnection("appointments", ApptBase),
        "ehr": DBConnection("ehr", EhrBase),
        "billing": DBConnection("billing", BillingBase),
        "reporting": DBConnection("reporting", ReportBase),
    }

    # 1. Clear existing data
    for name, db in dbs.items():
        await db.init_db()

    # 2. RBAC
    rbac_data = {}
    async with dbs["rbac"].Session() as session:
        roles = [
            Role(
                name="Admin",
                description="Super Admin",
                permissions={"all": ["*"]},
            ),
            Role(
                name="Physician",
                description="Doctor",
                permissions={"ehr": ["read", "write"]},
            ),
            Role(
                name="Patient",
                description="Patient",
                permissions={"portal": ["read"]},
            ),
            Role(
                name="Biller",
                description="Billing Staff",
                permissions={"billing": ["read", "write"]},
            ),
        ]
        session.add_all(roles)
        await session.commit()
        role_map = {r.name: r.id for r in roles}

        clinic = Clinic(
            name="General Hospital", address={"city": "New York"}
        )
        session.add(clinic)
        await session.commit()

        loc = Location(
            clinic_id=clinic.id,
            name="Main",
            type="Hospital",
            address={},
        )
        session.add(loc)

        providers = []
        for i in range(5):
            u = User(
                role_id=role_map["Physician"],
                email=f"doc{i}@test.com",
                password_hash=pwd_context.hash("password"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_provider=True,
                is_active=True,
            )
            providers.append(u)

        admin = User(
            role_id=role_map["Admin"],
            email="admin@test.com",
            password_hash=pwd_context.hash("admin"),
            first_name="Admin",
            last_name="User",
            is_active=True,
        )

        session.add_all(providers + [admin])
        await session.commit()
        rbac_data["providers"] = [str(p.id) for p in providers]
        rbac_data["patient_role"] = role_map["Patient"]

    # 3. Patients
    patient_ids = []
    async with (
        dbs["rbac"].Session() as rbac_sess,
        dbs["patient"].Session() as pat_sess,
        dbs["reporting"].Session() as rep_sess,
    ):
        for _ in range(50):
            # RBAC User for patient
            p_user = User(
                role_id=rbac_data["patient_role"],
                email=fake.email(),
                password_hash=pwd_context.hash("password"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_active=True,
            )
            rbac_sess.add(p_user)
            await rbac_sess.flush()

            pat = Patient(
                id=str(uuid.uuid4()),
                user_id=str(p_user.id),
                first_name=p_user.first_name,
                last_name=p_user.last_name,
                mrn=fake.bothify("MRN-#####"),
                email=p_user.email,
                is_active=True,
                insurance={"provider": "BlueCross", "policy": "123"},
            )
            pat_sess.add(pat)
            patient_ids.append(pat.id)

            # Reporting
            rep_sess.add(
                ReportingPatient(
                    id=pat.id,
                    is_active=True,
                    registration_date=date.today(),
                )
            )

        await rbac_sess.commit()
        await pat_sess.commit()
        await rep_sess.commit()

    # 4. Appointments & Clinical
    async with (
        dbs["appointments"].Session() as appt_sess,
        dbs["ehr"].Session() as ehr_sess,
        dbs["billing"].Session() as bill_sess,
        dbs["reporting"].Session() as rep_sess,
    ):
        # Schedules
        for pid in rbac_data["providers"]:
            for d in range(5):
                appt_sess.add(
                    ProviderSchedule(
                        provider_id=pid,
                        day_of_week=d,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                    )
                )

        # Appointments
        for _ in range(150):
            is_past = random.choice([True, False])
            start_date = (
                fake.date_between(start_date="-30d", end_date="-1d")
                if is_past
                else fake.date_between(
                    start_date="today", end_date="+30d"
                )
            )
            start_time = datetime.combine(
                start_date, time(random.randint(9, 16), 0)
            )

            pat_id = random.choice(patient_ids)
            prov_id = random.choice(rbac_data["providers"])
            status = "completed" if is_past else "scheduled"

            appt_id = str(uuid.uuid4())
            appt = Appointment(
                id=appt_id,
                patient_id=pat_id,
                provider_id=prov_id,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=30),
                appointment_type="initial",
                status=status,
            )
            appt_sess.add(appt)

            rep_sess.add(
                ReportingAppointment(
                    id=appt_id,
                    patient_id=pat_id,
                    provider_id=prov_id,
                    start_time=start_time,
                    date_only=start_date,
                    appointment_type="initial",
                    status=status,
                )
            )

            if status == "completed":
                # EHR
                enc_id = str(uuid.uuid4())
                ehr_sess.add(
                    Encounter(
                        id=enc_id,
                        appointment_id=appt_id,
                        patient_id=pat_id,
                        provider_id=prov_id,
                        date=start_time,
                        subjective="Patient complained of cough.",
                        diagnosis_codes=[
                            {"code": "J00", "description": "Cold"}
                        ],
                    )
                )

                # Billing
                tx_id = str(uuid.uuid4())
                bill_sess.add(
                    Transaction(
                        id=tx_id,
                        patient_id=pat_id,
                        appointment_id=appt_id,
                        type="CHARGE",
                        amount=150.0,
                        status="success",
                    )
                )
                rep_sess.add(
                    ReportingTransaction(
                        id=tx_id,
                        patient_id=pat_id,
                        type="CHARGE",
                        amount=150.0,
                        status="success",
                        transaction_date=start_date,
                    )
                )

        await appt_sess.commit()
        await ehr_sess.commit()
        await bill_sess.commit()
        await rep_sess.commit()

    for db in dbs.values():
        await db.close()

    logger.info("✅ Seeding Complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
