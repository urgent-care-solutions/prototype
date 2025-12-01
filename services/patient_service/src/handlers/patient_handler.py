import logging
import uuid

from faststream.nats import NatsBroker

from shared.messages import (
    AuditLog,
    PatientCreate,
    PatientCreated,
    PatientDelete,
    PatientDeleted,
    PatientRead,
    PatientReaded,
    PatientUpdate,
    PatientUpdated,
)
from src.config import settings
from src.services.patient_service import PatientService

_log = logging.getLogger(settings.LOGGER)


def register_handlers(broker: NatsBroker):

    @broker.subscriber("patient.create")
    @broker.publisher("patient.created")
    @broker.publisher("audit.log.patient")
    async def handle_patient_create(
        msg: PatientCreate,
    ) -> PatientCreated:
        _log.info(f"Creating patient with MRN: {msg.mrn}")
        try:
            patient = await PatientService.create_patient(msg)

            # Publish Audit
            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="patient",
                    resource_id=patient.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={"mrn": patient.mrn},
                ),
                subject="audit.log.patient",
            )

            return PatientCreated.model_validate(
                patient, from_attributes=True
            )
        except Exception as e:
            _log.error(f"Error creating patient: {e}")
            return PatientCreated(
                id=uuid.uuid4(),
                success=False,
                first_name=msg.first_name,
                last_name=msg.last_name,
                mrn=msg.mrn,
            )

    @broker.subscriber("patient.read")
    @broker.publisher("patient.readed")
    async def handle_patient_read(msg: PatientRead) -> PatientReaded:
        _log.debug(f"Reading patient: {msg.patient_id}")
        patient = await PatientService.get_patient(msg.patient_id)
        if not patient:
            return PatientReaded(
                success=False, first_name="", last_name="", mrn=""
            )
        return PatientReaded.model_validate(
            patient, from_attributes=True
        )

    @broker.subscriber("patient.update")
    @broker.publisher("patient.updated")
    @broker.publisher("audit.log.patient")
    async def handle_patient_update(
        msg: PatientUpdate,
    ) -> PatientUpdated:
        _log.info(f"Updating patient: {msg.patient_id}")
        try:
            patient = await PatientService.update_patient(msg)

            await broker.publish(
                AuditLog(
                    action="UPDATE",
                    resource_type="patient",
                    resource_id=patient.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "updated_fields": msg.model_dump(
                            exclude_unset=True
                        ).keys()
                    },
                ),
                subject="audit.log.patient",
            )

            return PatientUpdated.model_validate(
                patient, from_attributes=True
            )
        except Exception as e:
            _log.error(f"Error updating patient: {e}")
            return PatientUpdated(
                success=False,
                id=msg.patient_id,
                first_name="",
                last_name="",
                mrn="",
            )

    @broker.subscriber("patient.delete")
    @broker.publisher("patient.deleted")
    @broker.publisher("audit.log.patient")
    async def handle_patient_delete(
        msg: PatientDelete,
    ) -> PatientDeleted:
        _log.info(f"Deleting patient: {msg.patient_id}")
        try:
            patient = await PatientService.delete_patient(
                msg.patient_id
            )

            await broker.publish(
                AuditLog(
                    action="DELETE",
                    resource_type="patient",
                    resource_id=patient.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                ),
                subject="audit.log.patient",
            )

            return PatientDeleted(patient_id=patient.id, success=True)
        except Exception as e:
            _log.error(f"Error deleting patient: {e}")
            return PatientDeleted(
                patient_id=msg.patient_id, success=False
            )
