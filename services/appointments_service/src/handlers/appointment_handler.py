import logging
import uuid
from datetime import datetime

from faststream.nats import NatsBroker

from shared.messages import (
    AppointmentCancel,
    AppointmentCanceled,
    AppointmentCreate,
    AppointmentCreated,
    AppointmentRead,
    AppointmentReaded,
    AuditLog,
    AvailabilityRequest,
    AvailabilityResponse,
    ScheduleCreate,
    ScheduleCreated,
)
from src.config import settings
from src.services.appointment_service import AppointmentService
from src.services.schedule_service import ScheduleService

_log = logging.getLogger(settings.LOGGER)


def register_handlers(broker: NatsBroker):
    # --- Appointments ---

    @broker.subscriber("appointment.create")
    @broker.publisher("appointment.created")
    @broker.publisher("audit.log.appointment")
    async def handle_create_appointment(
        msg: AppointmentCreate,
    ) -> AppointmentCreated:
        _log.info(f"Request to create appointment for patient {msg.patient_id}")
        try:
            apt = await AppointmentService.create_appointment(msg)

            # Audit
            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="appointment",
                    resource_id=apt.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "provider_id": msg.provider_id,
                        "type": msg.appointment_type,
                    },
                ),
                subject="audit.log.appointment",
            )

            return AppointmentCreated.model_validate(apt, from_attributes=True)
        except ValueError as e:
            _log.error(f"Business error creating appointment: {e}")
            return AppointmentCreated(
                id=uuid.uuid4(),  # dummy
                success=False,
                error=str(e),
                patient_id=msg.patient_id,
                provider_id=msg.provider_id,
                start_time=msg.start_time,
                appointment_type=msg.appointment_type,
                end_time=msg.start_time,  # dummy
            )
        except Exception as e:
            _log.error(f"System error creating appointment: {e}")
            return AppointmentCreated(
                id=uuid.uuid4(),  # dummy
                success=False,
                error="Internal Server Error",
                patient_id=msg.patient_id,
                provider_id=msg.provider_id,
                start_time=msg.start_time,
                appointment_type=msg.appointment_type,
                end_time=msg.start_time,
            )

    @broker.subscriber("appointment.cancel")
    @broker.publisher("appointment.canceled")
    @broker.publisher("audit.log.appointment")
    async def handle_cancel_appointment(
        msg: AppointmentCancel,
    ) -> AppointmentCanceled:
        _log.info(f"Canceling appointment {msg.appointment_id}")
        try:
            await AppointmentService.cancel_appointment(msg)

            await broker.publish(
                AuditLog(
                    action="UPDATE",  # Logic status change
                    resource_type="appointment",
                    resource_id=msg.appointment_id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "status": "canceled",
                        "reason": msg.reason,
                    },
                ),
                subject="audit.log.appointment",
            )
            return AppointmentCanceled(appointment_id=msg.appointment_id, success=True)
        except Exception as e:
            _log.error(f"Error canceling appointment: {e}")
            return AppointmentCanceled(appointment_id=msg.appointment_id, success=False)

    @broker.subscriber("appointment.read")
    @broker.publisher("appointment.readed")
    async def handle_read_appointment(
        msg: AppointmentRead,
    ) -> AppointmentReaded:
        apt = await AppointmentService.get_appointment(msg.appointment_id)
        if not apt:
            return AppointmentReaded(
                success=False,
                appointment_id=msg.appointment_id,
                patient_id=uuid.uuid4(),  # dummy
                provider_id=uuid.uuid4(),  # dummy
                start_time=datetime.now(),
                appointment_type="initial",
                end_time=datetime.now(),
            )
        return AppointmentReaded.model_validate(apt, from_attributes=True)

    # --- Schedules / Availability ---

    @broker.subscriber("schedule.create")
    @broker.publisher("schedule.created")
    @broker.publisher("audit.log.schedule")
    async def handle_create_schedule(
        msg: ScheduleCreate,
    ) -> ScheduleCreated:
        # NOTE: Caller (API Gateway/RBAC) should verify user is ADMIN or the Provider themselves
        _log.info(f"Creating schedule for provider {msg.provider_id}")
        try:
            sch = await ScheduleService.create_schedule(msg)

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="schedule",
                    resource_id=sch.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "day": msg.day_of_week,
                        "start": str(msg.start_time),
                    },
                ),
                subject="audit.log.schedule",
            )

            return ScheduleCreated.model_validate(sch, from_attributes=True)
        except Exception as e:
            _log.error(f"Error creating schedule: {e}")
            return ScheduleCreated(
                success=False,
                provider_id=msg.provider_id,
                day_of_week=msg.day_of_week,
                start_time=msg.start_time,
                end_time=msg.end_time,
            )

    @broker.subscriber("availability.get")
    @broker.publisher("availability.response")
    async def handle_get_availability(
        msg: AvailabilityRequest,
    ) -> AvailabilityResponse:
        slots = await ScheduleService.get_availability(msg)
        return AvailabilityResponse(
            provider_id=msg.provider_id, date=msg.date, slots=slots
        )
