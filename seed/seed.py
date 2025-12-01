import asyncio
import random
import sys
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

from faker import Faker
from passlib.context import CryptContext
from rich.console import Console
from rich.progress import track
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Dynamic Model Imports ---
# Importing models dynamically to avoid import conflicts with 'src' modules
from services.appointments_service.src.models import (
    Appointment,
    ProviderSchedule,
)
from services.appointments_service.src.models import Base as ApptBase
from services.audit_service.src.models import Base as AuditBase
from services.ehr_service.src.models import Base as EhrBase
from services.ehr_service.src.models import (
    Encounter,
    Prescription,
    Vitals,
)
from services.integration_service.src.models import Base as BillingBase
from services.integration_service.src.models import Transaction
from services.notification_service.src.models import Base as NotifBase
from services.patient_service.src.models import Base as PatientBase
from services.patient_service.src.models import Patient
from services.rbac_service.src.models import Base as RbacBase
from services.rbac_service.src.models import (
    Clinic,
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

# --- Configuration & Setup ---

ROOT_DIR = Path.cwd()
sys.path.append(str(ROOT_DIR))

console = Console()
fake = Faker()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database Paths (Based on your .env and configs)
DB_PATHS = {
    "rbac": ROOT_DIR / "services/rbac_service/database/rbac.db",
    "patient": ROOT_DIR
    / "services/patient_service/src/database/patients.db",
    "appointments": ROOT_DIR
    / "services/appointments_service/src/database/appointments.db",
    "ehr": ROOT_DIR / "services/ehr_service/database/ehr.db",
    "billing": ROOT_DIR
    / "services/integration_service/database/integration.db",
    "notification": ROOT_DIR
    / "services/notification_service/database/notification.db",
    "reporting": ROOT_DIR
    / "services/reporting_service/database/reporting.db",
    "audit": ROOT_DIR / "services/audit_service/database/audit.db",
}

# Ensure directories exist
for db_path in DB_PATHS.values():
    db_path.parent.mkdir(parents=True, exist_ok=True)

# --- Database Helper ---


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
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)
            await conn.run_sync(self.base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()


# --- Data Generation Logic ---


async def seed_data():
    console.rule("[bold green]Starting System Seed")

    # 1. Initialize Databases
    dbs = {
        "rbac": DBConnection("rbac", RbacBase),
        "patient": DBConnection("patient", PatientBase),
        "appointments": DBConnection("appointments", ApptBase),
        "ehr": DBConnection("ehr", EhrBase),
        "billing": DBConnection("billing", BillingBase),
        "notification": DBConnection("notification", NotifBase),
        "reporting": DBConnection("reporting", ReportBase),
        "audit": DBConnection("audit", AuditBase),
    }

    for name, db in dbs.items():
        console.print(f"🧹 Resetting database: [bold]{name}[/bold]")
        await db.init_db()

    # --- 2. RBAC Seeding ---
    console.rule("[bold blue]Seeding RBAC Service")

    rbac_data = {}

    async with dbs["rbac"].Session() as session:
        # Roles
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
                name="Nurse",
                description="Nurse",
                permissions={"ehr": ["read"]},
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

        # Clinic Structure
        clinic = Clinic(
            name="Metropolis General Hospital",
            email="contact@metro-general.com",
            address={
                "street": "123 Hero Ln",
                "city": "Metropolis",
                "state": "NY",
            },
            timezone="America/New_York",
        )
        session.add(clinic)
        await session.commit()

        loc_main = Location(
            clinic_id=clinic.id,
            name="Main Campus",
            type="Hospital",
            address={"street": "123 Hero Ln"},
        )
        loc_north = Location(
            clinic_id=clinic.id,
            name="North Wing",
            type="Clinic",
            address={"street": "456 North Ave"},
        )
        session.add_all([loc_main, loc_north])
        await session.commit()

        # Users - Providers
        providers = []
        for _ in range(5):
            u = User(
                role_id=role_map["Physician"],
                email=fake.email(),
                password_hash=pwd_context.hash("password"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_provider=True,
                provider_npi=fake.numerify("##########"),
                is_active=True,
            )
            providers.append(u)

        # Users - Staff
        billers = []
        for _ in range(2):
            u = User(
                role_id=role_map["Biller"],
                email=fake.email(),
                password_hash=pwd_context.hash("password"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_active=True,
            )
            billers.append(u)

        # Users - Admin
        admin = User(
            role_id=role_map["Admin"],
            email="admin@system.com",
            password_hash=pwd_context.hash("admin"),
            first_name="Super",
            last_name="Admin",
            is_active=True,
        )

        session.add_all(providers + billers + [admin])
        await session.commit()

        rbac_data["providers"] = [str(p.id) for p in providers]
        rbac_data["role_patient"] = role_map["Patient"]

    # --- 3. Patient Seeding ---
    console.rule("[bold blue]Seeding Patient Service")

    patient_ids = []

    # We need to create Users for patients first in RBAC, then create Patient records
    async with (
        dbs["rbac"].Session() as rbac_sess,
        dbs["patient"].Session() as pat_sess,
        dbs["reporting"].Session() as rep_sess,
    ):
        for _ in track(range(50), description="Creating Patients..."):
            # RBAC User
            p_user = User(
                role_id=rbac_data["role_patient"],
                email=fake.email(),
                password_hash=pwd_context.hash("password"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_active=True,
            )
            rbac_sess.add(p_user)
            await rbac_sess.flush()  # get ID

            # Patient Record
            reg_date = fake.date_between(
                start_date="-2y", end_date="today"
            )
            pat = Patient(
                id=str(uuid.uuid4()),
                user_id=str(p_user.id),
                first_name=p_user.first_name,
                last_name=p_user.last_name,
                mrn=fake.bothify("MRN-#####"),
                email=p_user.email,
                is_active=True,
                created_at=datetime.combine(reg_date, time(9, 0)),
                insurance={
                    "provider": fake.company(),
                    "policy_number": fake.bothify("POL-########"),
                },
            )
            pat_sess.add(pat)
            patient_ids.append(pat.id)

            # Reporting Record (Mirror)
            rep_pat = ReportingPatient(
                id=pat.id,
                is_active=True,
                registration_date=reg_date,
                created_at=datetime.now(),
            )
            rep_sess.add(rep_pat)

        await rbac_sess.commit()
        await pat_sess.commit()
        await rep_sess.commit()

    # --- 4. Schedules & Appointments ---
    console.rule("[bold blue]Seeding Appointments & Schedules")

    appointments_to_process = []  # (appt_id, patient_id, provider_id, date, status)

    async with (
        dbs["appointments"].Session() as appt_sess,
        dbs["reporting"].Session() as rep_sess,
    ):
        # Create Provider Schedules
        for prov_id in rbac_data["providers"]:
            for day in range(5):  # Mon-Fri
                sch = ProviderSchedule(
                    provider_id=prov_id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                    is_active=True,
                )
                appt_sess.add(sch)

        # Create Appointments (Past & Future)
        appt_types = ["initial", "follow_up", "telemedicine"]

        for _ in track(
            range(200), description="Generating Appointments..."
        ):
            is_past = random.choice([
                True,
                True,
                False,
            ])  # Bias towards past for clinical data

            if is_past:
                appt_date = fake.date_between(
                    start_date="-1y", end_date="-1d"
                )
                status = random.choice([
                    "completed",
                    "completed",
                    "completed",
                    "canceled",
                    "no_show",
                ])
            else:
                appt_date = fake.date_between(
                    start_date="today", end_date="+30d"
                )
                status = "scheduled"

            start_time = datetime.combine(
                appt_date,
                time(random.randint(9, 16), random.choice([0, 30])),
            )
            end_time = start_time + timedelta(minutes=30)

            pat_id = random.choice(patient_ids)
            prov_id = random.choice(rbac_data["providers"])
            a_type = random.choice(appt_types)
            a_id = str(uuid.uuid4())

            appt = Appointment(
                id=a_id,
                patient_id=pat_id,
                provider_id=prov_id,
                start_time=start_time,
                end_time=end_time,
                appointment_type=a_type,
                status=status,
                reason=fake.sentence(),
                created_at=start_time - timedelta(days=5),
            )
            appt_sess.add(appt)

            # Reporting Mirror
            rep_appt = ReportingAppointment(
                id=a_id,
                patient_id=pat_id,
                provider_id=prov_id,
                start_time=start_time,
                date_only=appt_date,
                appointment_type=a_type,
                status=status,
            )
            rep_sess.add(rep_appt)

            if status == "completed":
                appointments_to_process.append((
                    a_id,
                    pat_id,
                    prov_id,
                    start_time,
                ))

        await appt_sess.commit()
        await rep_sess.commit()

    # --- 5. EHR (Encounters) ---
    console.rule("[bold blue]Seeding Clinical Data (EHR)")

    async with dbs["ehr"].Session() as ehr_sess:
        diagnosis_pool = [
            {"code": "J00", "description": "Common Cold"},
            {"code": "I10", "description": "Hypertension"},
            {"code": "E11", "description": "Type 2 Diabetes"},
            {"code": "R51", "description": "Headache"},
        ]
        meds_pool = [
            "Amoxicillin",
            "Lisinopril",
            "Metformin",
            "Ibuprofen",
        ]

        for appt_id, pat_id, prov_id, date_time in track(
            appointments_to_process,
            description="Documenting Encounters...",
        ):
            # Encounter
            enc_id = str(uuid.uuid4())
            enc = Encounter(
                id=enc_id,
                appointment_id=appt_id,
                patient_id=pat_id,
                provider_id=prov_id,
                date=date_time,
                subjective=fake.paragraph(),
                objective="Patient appears well developed and well nourished.",
                assessment=fake.sentence(),
                plan="Rest and fluids.",
                diagnosis_codes=[random.choice(diagnosis_pool)],
            )
            ehr_sess.add(enc)

            # Vitals
            ehr_sess.add(
                Vitals(
                    patient_id=pat_id,
                    encounter_id=enc_id,
                    height_cm=random.uniform(150, 190),
                    weight_kg=random.uniform(50, 100),
                    systolic=random.randint(110, 140),
                    diastolic=random.randint(70, 90),
                    temperature_c=37.0,
                    heart_rate=random.randint(60, 100),
                )
            )

            # Prescriptions (Randomly)
            if random.random() > 0.6:
                ehr_sess.add(
                    Prescription(
                        encounter_id=enc_id,
                        patient_id=pat_id,
                        provider_id=prov_id,
                        medication_name=random.choice(meds_pool),
                        dosage="500mg",
                        frequency="Daily",
                        duration_days=10,
                    )
                )

        await ehr_sess.commit()

    # --- 6. Billing & Reporting ---
    console.rule("[bold blue]Seeding Billing & Financial Reports")

    async with (
        dbs["billing"].Session() as bill_sess,
        dbs["reporting"].Session() as rep_sess,
    ):
        for appt_id, pat_id, prov_id, date_time in track(
            appointments_to_process, description="Generating Charges..."
        ):
            amount = round(random.uniform(100.0, 300.0), 2)
            tx_id = str(uuid.uuid4())

            # Create Charge
            charge = Transaction(
                id=tx_id,
                patient_id=pat_id,
                appointment_id=appt_id,
                type="CHARGE",
                amount=amount,
                status="success",
                description="Consultation Fee",
            )
            bill_sess.add(charge)

            # Reporting Mirror (Charge)
            rep_sess.add(
                ReportingTransaction(
                    id=tx_id,
                    patient_id=pat_id,
                    type="CHARGE",
                    amount=amount,
                    status="success",
                    transaction_date=date_time.date(),
                )
            )

            # Random Refund
            if random.random() > 0.95:
                ref_id = str(uuid.uuid4())
                bill_sess.add(
                    Transaction(
                        id=ref_id,
                        patient_id=pat_id,
                        appointment_id=appt_id,
                        reference_id=tx_id,
                        type="REFUND",
                        amount=amount,
                        status="success",
                        description="Administrative Adjustment",
                    )
                )

                # Reporting Mirror (Refund)
                rep_sess.add(
                    ReportingTransaction(
                        id=ref_id,
                        patient_id=pat_id,
                        type="REFUND",
                        amount=amount,
                        status="success",
                        transaction_date=date_time.date(),
                    )
                )

        await bill_sess.commit()
        await rep_sess.commit()

    # --- Cleanup ---
    for db in dbs.values():
        await db.close()

    console.rule("[bold green]Seeding Complete")
    console.print(f"Created {len(rbac_data['providers'])} Providers")
    console.print(f"Created {len(patient_ids)} Patients")
    console.print(
        f"Created {len(appointments_to_process)} Completed Encounters/Charges"
    )
    console.print(
        "\n[bold]Log in with:[/bold] admin@system.com / admin"
    )


if __name__ == "__main__":
    asyncio.run(seed_data())
