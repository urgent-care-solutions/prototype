import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Encounter, Prescription, Vitals

from shared.messages import (
    DiagnosisCode,
    EncounterCreate,
    PrescriptionCreate,
    VitalsCreate,
)

_log = logging.getLogger(settings.LOGGER)


class EHRService:
    @staticmethod
    async def create_encounter(data: EncounterCreate) -> Encounter:
        async with AsyncSessionLocal() as session:
            # Prepare diagnosis codes for JSON storage
            codes_json = [
                {"code": d.code, "description": d.description}
                for d in data.diagnosis_codes
            ]

            encounter = Encounter(
                appointment_id=str(data.appointment_id)
                if data.appointment_id
                else None,
                patient_id=str(data.patient_id),
                provider_id=str(data.provider_id),
                date=data.date,
                subjective=data.subjective,
                objective=data.objective,
                assessment=data.assessment,
                plan=data.plan,
                diagnosis_codes=codes_json,
            )
            session.add(encounter)
            await session.commit()
            await session.refresh(encounter)
            return encounter

    @staticmethod
    async def get_encounter(encounter_id: UUID) -> Encounter | None:
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Encounter)
                .options(
                    selectinload(Encounter.vitals),
                    selectinload(Encounter.prescriptions),
                )
                .where(Encounter.id == str(encounter_id))
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def add_vitals(data: VitalsCreate) -> Vitals:
        async with AsyncSessionLocal() as session:
            vitals = Vitals(
                encounter_id=str(data.encounter_id)
                if data.encounter_id
                else None,
                patient_id=str(data.patient_id),
                height_cm=data.height_cm,
                weight_kg=data.weight_kg,
                temperature_c=data.temperature_c,
                systolic=data.systolic,
                diastolic=data.diastolic,
                heart_rate=data.heart_rate,
                respiratory_rate=data.respiratory_rate,
                oxygen_saturation=data.oxygen_saturation,
            )
            session.add(vitals)
            await session.commit()
            await session.refresh(vitals)
            return vitals

    @staticmethod
    async def add_prescription(
        data: PrescriptionCreate,
    ) -> Prescription:
        async with AsyncSessionLocal() as session:
            rx = Prescription(
                encounter_id=str(data.encounter_id)
                if data.encounter_id
                else None,
                patient_id=str(data.patient_id),
                provider_id=str(data.provider_id),
                medication_name=data.medication_name,
                dosage=data.dosage,
                frequency=data.frequency,
                duration_days=data.duration_days,
                instructions=data.instructions,
                status=data.status,
            )
            session.add(rx)
            await session.commit()
            await session.refresh(rx)
            return rx

    @staticmethod
    def search_diagnosis_codes(query: str) -> list[DiagnosisCode]:
        # Mock Data Source
        mock_db = [
            DiagnosisCode(
                code="J00",
                description="Acute nasopharyngitis [common cold]",
            ),
            DiagnosisCode(
                code="J01.90",
                description="Acute sinusitis, unspecified",
            ),
            DiagnosisCode(
                code="J02.9",
                description="Acute pharyngitis, unspecified",
            ),
            DiagnosisCode(
                code="J18.9",
                description="Pneumonia, unspecified organism",
            ),
            DiagnosisCode(
                code="J20.9",
                description="Acute bronchitis, unspecified",
            ),
            DiagnosisCode(
                code="J45.909",
                description="Unspecified asthma, uncomplicated",
            ),
            DiagnosisCode(
                code="I10",
                description="Essential (primary) hypertension",
            ),
            DiagnosisCode(
                code="E11.9",
                description="Type 2 diabetes mellitus without complications",
            ),
            DiagnosisCode(code="R51", description="Headache"),
            DiagnosisCode(code="R05", description="Cough"),
            DiagnosisCode(
                code="R50.9", description="Fever, unspecified"
            ),
            DiagnosisCode(code="M54.5", description="Low back pain"),
            DiagnosisCode(
                code="Z00.00",
                description="Encounter for general adult medical exam",
            ),
        ]

        if not query:
            return mock_db[:10]

        query = query.lower()
        return [
            d
            for d in mock_db
            if query in d.code.lower() or query in d.description.lower()
        ]
