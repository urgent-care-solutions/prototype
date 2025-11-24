import logging
import uuid
from datetime import datetime

from faststream.nats import NatsBroker
from src.config import settings
from src.services.ehr_service import EHRService

from shared.messages import (
    AuditLog,
    DiagnosisResponse,
    DiagnosisSearch,
    EncounterCreate,
    EncounterCreated,
    EncounterRead,
    EncounterReaded,
    PrescriptionCreate,
    PrescriptionCreated,
    VitalsCreate,
    VitalsCreated,
)

_log = logging.getLogger(settings.LOGGER)


def register_handlers(broker: NatsBroker):

    @broker.subscriber("ehr.encounter.create")
    @broker.publisher("ehr.encounter.created")
    @broker.publisher("audit.log.encounter")
    async def handle_create_encounter(
        msg: EncounterCreate,
    ) -> EncounterCreated:
        _log.info(f"Creating encounter for patient {msg.patient_id}")
        try:
            encounter = await EHRService.create_encounter(msg)

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="encounter",
                    resource_id=encounter.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "appointment_id": str(msg.appointment_id)
                        if msg.appointment_id
                        else None
                    },
                ),
                subject="audit.log.encounter",
            )

            return EncounterCreated.model_validate(
                encounter, from_attributes=True
            )
        except Exception as e:
            _log.error(f"Error creating encounter: {e}")
            return EncounterCreated(
                success=False,
                patient_id=msg.patient_id,
                provider_id=msg.provider_id,
                date=msg.date,
            )

    @broker.subscriber("ehr.encounter.read")
    @broker.publisher("ehr.encounter.readed")
    async def handle_read_encounter(
        msg: EncounterRead,
    ) -> EncounterReaded:
        encounter = await EHRService.get_encounter(msg.encounter_id)
        if not encounter:
            return EncounterReaded(
                success=False,
                id=msg.encounter_id,
                patient_id=uuid.uuid4(),  # Dummy
                provider_id=uuid.uuid4(),
                date=datetime.now(),
            )

        # Manually validate because of relationships
        response = EncounterReaded.model_validate(
            encounter, from_attributes=True
        )
        response.vitals = [
            VitalsCreated.model_validate(v, from_attributes=True)
            for v in encounter.vitals
        ]
        response.prescriptions = [
            PrescriptionCreated.model_validate(p, from_attributes=True)
            for p in encounter.prescriptions
        ]
        return response

    @broker.subscriber("ehr.vitals.add")
    @broker.publisher("ehr.vitals.added")
    @broker.publisher("audit.log.vitals")
    async def handle_add_vitals(msg: VitalsCreate) -> VitalsCreated:
        _log.info(f"Adding vitals for patient {msg.patient_id}")
        try:
            vitals = await EHRService.add_vitals(msg)

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="vitals",
                    resource_id=vitals.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "encounter_id": str(msg.encounter_id)
                        if msg.encounter_id
                        else None
                    },
                ),
                subject="audit.log.vitals",
            )
            return VitalsCreated.model_validate(
                vitals, from_attributes=True
            )
        except Exception as e:
            _log.error(f"Error adding vitals: {e}")
            return VitalsCreated(
                success=False, patient_id=msg.patient_id
            )

    @broker.subscriber("ehr.prescription.add")
    @broker.publisher("ehr.prescription.added")
    @broker.publisher("audit.log.prescription")
    async def handle_add_prescription(
        msg: PrescriptionCreate,
    ) -> PrescriptionCreated:
        _log.info(f"Adding prescription for patient {msg.patient_id}")
        try:
            rx = await EHRService.add_prescription(msg)

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="prescription",
                    resource_id=rx.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={"medication": msg.medication_name},
                ),
                subject="audit.log.prescription",
            )
            return PrescriptionCreated.model_validate(
                rx, from_attributes=True
            )
        except Exception as e:
            _log.error(f"Error adding prescription: {e}")
            return PrescriptionCreated(
                success=False,
                patient_id=msg.patient_id,
                provider_id=msg.provider_id,
                medication_name=msg.medication_name,
                dosage=msg.dosage,
                frequency=msg.frequency,
                duration_days=msg.duration_days,
            )

    @broker.subscriber("ehr.diagnosis.search")
    @broker.publisher("ehr.diagnosis.results")
    async def handle_diagnosis_search(
        msg: DiagnosisSearch,
    ) -> DiagnosisResponse:
        results = EHRService.search_diagnosis_codes(msg.query)
        return DiagnosisResponse(results=results)
