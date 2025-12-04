import logging
from datetime import datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, select

from shared.messages import (
    AvailabilityRequest,
    ScheduleCreate,
    TimeSlot,
)
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Appointment, ProviderSchedule

_log = logging.getLogger(settings.LOGGER)


class ScheduleService:
    @staticmethod
    async def create_schedule(data: ScheduleCreate) -> ProviderSchedule:
        async with AsyncSessionLocal() as session:
            # Check for overlapping schedules for same provider/day
            stmt = select(ProviderSchedule).where(
                and_(
                    ProviderSchedule.provider_id == str(data.provider_id),
                    ProviderSchedule.day_of_week == data.day_of_week,
                    ProviderSchedule.is_active == True,  # noqa: E712
                )
            )
            existing = await session.execute(stmt)
            for sch in existing.scalars():
                # Simple overlap check: if new start < old end and new end > old start
                if data.start_time < sch.end_time and data.end_time > sch.start_time:
                    raise ValueError("Schedule overlaps with existing rule")

            schedule = ProviderSchedule(
                provider_id=str(data.provider_id),
                day_of_week=data.day_of_week,
                start_time=data.start_time,
                end_time=data.end_time,
                is_active=data.is_active,
            )
            session.add(schedule)
            await session.commit()
            await session.refresh(schedule)
            return schedule

    @staticmethod
    async def get_availability(
        req: AvailabilityRequest,
    ) -> list[TimeSlot]:
        """
        Calculates available slots for a provider on a specific date.
        1. Get provider's schedule rule for that day of week.
        2. Generate 30-min slots (default resolution).
        3. Fetch existing appointments.
        4. Subtract booked time.
        """
        target_dow = req.date.weekday()  # 0=Monday

        async with AsyncSessionLocal() as session:
            # 1. Get Schedule
            stmt = select(ProviderSchedule).where(
                and_(
                    ProviderSchedule.provider_id == str(req.provider_id),
                    ProviderSchedule.day_of_week == target_dow,
                    ProviderSchedule.is_active == True,  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            schedules = result.scalars().all()

            if not schedules:
                return []

            # 2. Get existing appointments for that day
            day_start = datetime.combine(req.date, time.min)
            day_end = datetime.combine(req.date, time.max)

            apt_stmt = select(Appointment).where(
                and_(
                    Appointment.provider_id == str(req.provider_id),
                    Appointment.status == "scheduled",
                    Appointment.start_time >= day_start,
                    Appointment.start_time <= day_end,
                )
            )
            apt_result = await session.execute(apt_stmt)
            appointments = apt_result.scalars().all()

            available_slots = []

            # Simple slot generation strategy: 30 min intervals
            slot_duration = timedelta(minutes=30)

            for schedule in schedules:
                current_time = datetime.combine(req.date, schedule.start_time)
                end_time = datetime.combine(req.date, schedule.end_time)

                while current_time + slot_duration <= end_time:
                    slot_end = current_time + slot_duration

                    # Check overlap
                    is_booked = False
                    for apt in appointments:
                        # If overlap
                        if current_time < apt.end_time and slot_end > apt.start_time:
                            is_booked = True
                            break

                    if not is_booked:
                        available_slots.append(
                            TimeSlot(
                                start=current_time,
                                end=slot_end,
                                available=True,
                            )
                        )

                    current_time += slot_duration

            return available_slots

    @staticmethod
    async def list_schedules(provider_id: UUID):
        async with AsyncSessionLocal() as session:
            stmt = select(ProviderSchedule).where(
                and_(
                    ProviderSchedule.provider_id == str(provider_id),
                    ProviderSchedule.is_active == True,  # noqa: E712
                )
            )
            res = await session.execute(stmt)
            return res.scalars().all()
