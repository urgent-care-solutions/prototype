import logging
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, select

from shared.messages import AppointmentCancel, AppointmentCreate
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Appointment, ProviderSchedule

_log = logging.getLogger(settings.LOGGER)


class AppointmentService:
    @staticmethod
    async def create_appointment(
        data: AppointmentCreate,
    ) -> Appointment:
        # Determine duration
        duration_map = {
            "initial": settings.DURATION_INITIAL,
            "follow_up": settings.DURATION_FOLLOWUP,
            "telemedicine": settings.DURATION_TELEMEDICINE,
        }
        duration_minutes = duration_map.get(data.appointment_type, 30)
        end_time = data.start_time + timedelta(minutes=duration_minutes)

        async with AsyncSessionLocal() as session:
            # 1. Validate Provider Availability Rule
            dow = data.start_time.weekday()
            req_time = data.start_time.time()
            req_end_time = end_time.time()

            sched_stmt = select(ProviderSchedule).where(
                and_(
                    ProviderSchedule.provider_id
                    == str(data.provider_id),
                    ProviderSchedule.day_of_week == dow,
                    ProviderSchedule.is_active == True,  # noqa: E712
                    ProviderSchedule.start_time <= req_time,
                    ProviderSchedule.end_time >= req_end_time,
                )
            )
            sched_res = await session.execute(sched_stmt)
            if not sched_res.scalars().first():
                raise ValueError("Provider is not working at this time")

            # 2. Check for Overlaps with existing appointments
            # Logic: (StartA < EndB) and (EndA > StartB)
            overlap_stmt = select(Appointment).where(
                and_(
                    Appointment.provider_id == str(data.provider_id),
                    Appointment.status == "scheduled",
                    Appointment.start_time < end_time,
                    Appointment.end_time > data.start_time,
                )
            )
            overlap_res = await session.execute(overlap_stmt)
            if overlap_res.scalars().first():
                raise ValueError("Time slot is already booked")

            # 3. Create Appointment
            new_apt = Appointment(
                patient_id=str(data.patient_id),
                provider_id=str(data.provider_id),
                start_time=data.start_time,
                end_time=end_time,
                appointment_type=data.appointment_type,
                reason=data.reason,
                status="scheduled",
            )
            session.add(new_apt)
            await session.commit()
            await session.refresh(new_apt)

            _log.info(f"Appointment created: {new_apt.id}")
            return new_apt

    @staticmethod
    async def cancel_appointment(
        data: AppointmentCancel,
    ) -> Appointment:
        async with AsyncSessionLocal() as session:
            stmt = select(Appointment).where(
                Appointment.id == str(data.appointment_id)
            )
            res = await session.execute(stmt)
            apt = res.scalars().first()

            if not apt:
                raise ValueError("Appointment not found")

            if apt.status == "canceled":
                return apt  # Idempotent

            apt.status = "canceled"
            apt.cancellation_reason = data.reason

            await session.commit()
            await session.refresh(apt)
            _log.info(f"Appointment canceled: {apt.id}")
            return apt

    @staticmethod
    async def get_appointment(apt_id: UUID) -> Appointment | None:
        async with AsyncSessionLocal() as session:
            stmt = select(Appointment).where(
                Appointment.id == str(apt_id)
            )
            res = await session.execute(stmt)
            return res.scalars().first()
