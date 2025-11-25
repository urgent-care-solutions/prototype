import logging
from datetime import date

from sqlalchemy import and_, func, select
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import (
    ReportingAppointment,
    ReportingPatient,
    ReportingTransaction,
)

from shared.messages import (
    AppointmentCanceled,
    AppointmentCreated,
    AppointmentStats,
    ChargeCreated,
    PatientCreated,
    PatientDeleted,
    PatientStats,
    PatientUpdated,
    RefundCreated,
    RevenueStats,
)

_log = logging.getLogger(settings.LOGGER)


class ReportingService:
    # --- Ingestion Methods (Writes) ---

    @staticmethod
    async def ingest_appointment(msg: AppointmentCreated):
        async with AsyncSessionLocal() as session:
            # Check for idempotency
            exists = await session.get(
                ReportingAppointment, str(msg.id)
            )
            if exists:
                return

            appt = ReportingAppointment(
                id=str(msg.id),
                patient_id=str(msg.patient_id),
                provider_id=str(msg.provider_id),
                start_time=msg.start_time,
                date_only=msg.start_time.date(),
                appointment_type=msg.appointment_type,
                status="scheduled",
            )
            session.add(appt)
            await session.commit()
            _log.info(f"Ingested appointment {msg.id} for analytics")

    @staticmethod
    async def ingest_appointment_cancellation(msg: AppointmentCanceled):
        async with AsyncSessionLocal() as session:
            appt = await session.get(
                ReportingAppointment, str(msg.appointment_id)
            )
            if appt:
                appt.status = "canceled"
                await session.commit()
                _log.info(
                    f"Updated analytics for canceled appointment {msg.appointment_id}"
                )

    @staticmethod
    async def ingest_charge(msg: ChargeCreated):
        if not msg.success:
            return  # We only care about successful revenue

        async with AsyncSessionLocal() as session:
            exists = await session.get(
                ReportingTransaction, str(msg.transaction_id)
            )
            if exists:
                return

            tx = ReportingTransaction(
                id=str(msg.transaction_id),
                patient_id=str(msg.patient_id),
                type="CHARGE",
                amount=msg.amount,
                status="success",
                transaction_date=date.today(),  # Simplification: using ingestion time as date
            )
            session.add(tx)
            await session.commit()
            _log.info(
                f"Ingested charge {msg.transaction_id} for revenue analytics"
            )

    @staticmethod
    async def ingest_refund(msg: RefundCreated):
        if not msg.success:
            return

        async with AsyncSessionLocal() as session:
            exists = await session.get(
                ReportingTransaction, str(msg.refund_transaction_id)
            )
            if exists:
                return

            tx = ReportingTransaction(
                id=str(msg.refund_transaction_id),
                patient_id="unknown",  # Refund msg might not carry patient_id, usually inferred from original tx
                type="REFUND",
                amount=msg.amount,
                status="success",
                transaction_date=date.today(),
            )
            session.add(tx)
            await session.commit()

    @staticmethod
    async def ingest_patient(msg: PatientCreated):
        async with AsyncSessionLocal() as session:
            exists = await session.get(ReportingPatient, str(msg.id))
            if exists:
                return

            pat = ReportingPatient(
                id=str(msg.id),
                is_active=True,
                registration_date=date.today(),
            )
            session.add(pat)
            await session.commit()

    @staticmethod
    async def ingest_patient_update(msg: PatientUpdated):
        if msg.is_active is None:
            return

        async with AsyncSessionLocal() as session:
            pat = await session.get(ReportingPatient, str(msg.id))
            if pat:
                pat.is_active = msg.is_active
                await session.commit()

    @staticmethod
    async def ingest_patient_deletion(msg: PatientDeleted):
        async with AsyncSessionLocal() as session:
            pat = await session.get(
                ReportingPatient, str(msg.patient_id)
            )
            if pat:
                await session.delete(pat)
                await session.commit()

    # --- Analytics Methods (Reads) ---

    @staticmethod
    async def get_revenue_stats(
        start: date | None, end: date | None
    ) -> RevenueStats:
        async with AsyncSessionLocal() as session:
            filters = [ReportingTransaction.status == "success"]
            if start:
                filters.append(
                    ReportingTransaction.transaction_date >= start
                )
            if end:
                filters.append(
                    ReportingTransaction.transaction_date <= end
                )

            # Sum Charges
            charge_stmt = select(
                func.sum(ReportingTransaction.amount)
            ).where(
                and_(*filters, ReportingTransaction.type == "CHARGE")
            )
            refund_stmt = select(
                func.sum(ReportingTransaction.amount)
            ).where(
                and_(*filters, ReportingTransaction.type == "REFUND")
            )
            count_stmt = select(
                func.count(ReportingTransaction.id)
            ).where(and_(*filters))

            total_revenue = (
                await session.execute(charge_stmt)
            ).scalar() or 0.0
            total_refunds = (
                await session.execute(refund_stmt)
            ).scalar() or 0.0
            tx_count = (await session.execute(count_stmt)).scalar() or 0

            return RevenueStats(
                total_revenue=total_revenue,
                refund_amount=total_refunds,
                net_revenue=total_revenue - total_refunds,
                transaction_count=tx_count,
            )

    @staticmethod
    async def get_appointment_stats(
        start: date | None, end: date | None
    ) -> AppointmentStats:
        async with AsyncSessionLocal() as session:
            filters = []
            if start:
                filters.append(ReportingAppointment.date_only >= start)
            if end:
                filters.append(ReportingAppointment.date_only <= end)

            # Total
            total_stmt = select(
                func.count(ReportingAppointment.id)
            ).where(and_(*filters))
            total = (await session.execute(total_stmt)).scalar() or 0

            # By Status
            status_stmt = (
                select(
                    ReportingAppointment.status,
                    func.count(ReportingAppointment.id),
                )
                .where(and_(*filters))
                .group_by(ReportingAppointment.status)
            )

            status_res = (await session.execute(status_stmt)).all()
            by_status = {row[0]: row[1] for row in status_res}

            # By Type
            type_stmt = (
                select(
                    ReportingAppointment.appointment_type,
                    func.count(ReportingAppointment.id),
                )
                .where(and_(*filters))
                .group_by(ReportingAppointment.appointment_type)
            )

            type_res = (await session.execute(type_stmt)).all()
            by_type = {row[0]: row[1] for row in type_res}

            return AppointmentStats(
                total=total, by_status=by_status, by_type=by_type
            )

    @staticmethod
    async def get_patient_stats(
        start: date | None, end: date | None
    ) -> PatientStats:
        async with AsyncSessionLocal() as session:
            # Total Active
            active_stmt = select(func.count(ReportingPatient.id)).where(
                ReportingPatient.is_active == True  # noqa: E712
            )
            active = (await session.execute(active_stmt)).scalar() or 0

            # Total All Time
            total_stmt = select(func.count(ReportingPatient.id))
            total = (await session.execute(total_stmt)).scalar() or 0

            # New in period
            filters = []
            if start:
                filters.append(
                    ReportingPatient.registration_date >= start
                )
            if end:
                filters.append(
                    ReportingPatient.registration_date <= end
                )

            new_stmt = select(func.count(ReportingPatient.id)).where(
                and_(*filters)
            )
            new_in_period = (
                await session.execute(new_stmt)
            ).scalar() or 0

            return PatientStats(
                total_patients=total,
                active_patients=active,
                new_patients_in_period=new_in_period,
            )
