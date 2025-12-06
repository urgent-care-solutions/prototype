import logging

from faststream.nats import NatsBroker
from src.config import settings
from src.services.reporting_service import ReportingService

from shared.messages import (
    AppointmentCanceled,
    AppointmentCreated,
    AppointmentReportResponse,
    AuditLog,
    ChargeCreated,
    DateRangeRequest,
    PatientCreated,
    PatientDeleted,
    PatientReportResponse,
    PatientUpdated,
    RefundCreated,
    RevenueReportResponse,
)

_log = logging.getLogger(settings.LOGGER)


def register_handlers(broker: NatsBroker):
    # --- Ingestion Subscriptions ---

    @broker.subscriber("appointment.created")
    async def on_appointment_created(msg: AppointmentCreated):
        await ReportingService.ingest_appointment(msg)

    @broker.subscriber("appointment.canceled")
    async def on_appointment_canceled(msg: AppointmentCanceled):
        await ReportingService.ingest_appointment_cancellation(msg)

    @broker.subscriber("billing.charged")
    async def on_charge_created(msg: ChargeCreated):
        await ReportingService.ingest_charge(msg)

    @broker.subscriber("billing.refunded")
    async def on_refund_created(msg: RefundCreated):
        await ReportingService.ingest_refund(msg)

    @broker.subscriber("patient.created")
    async def on_patient_created(msg: PatientCreated):
        await ReportingService.ingest_patient(msg)

    @broker.subscriber("patient.updated")
    async def on_patient_updated(msg: PatientUpdated):
        await ReportingService.ingest_patient_update(msg)

    @broker.subscriber("patient.deleted")
    async def on_patient_deleted(msg: PatientDeleted):
        await ReportingService.ingest_patient_deletion(msg)

    # --- Reporting RPC Endpoints ---

    @broker.subscriber("report.revenue")
    @broker.publisher("audit.log.reporting")
    async def report_revenue(
        msg: DateRangeRequest,
    ) -> RevenueReportResponse:
        _log.info(f"Generating revenue report from {msg.start_date} to {msg.end_date}")
        stats = await ReportingService.get_revenue_stats(msg.start_date, msg.end_date)

        await broker.publish(
            AuditLog(
                action="READ",
                resource_type="reports",  # Note: 'reports' strictly isn't in Literal yet, using closest or should update AuditLog
                service_name=settings.SERVICE_NAME,
                user_id=msg.user_id,
                metadata={
                    "report": "revenue",
                    "range": f"{msg.start_date}-{msg.end_date}",
                },
            ),
            subject="audit.log.reporting",
        )

        return RevenueReportResponse(
            period_start=msg.start_date,
            period_end=msg.end_date,
            stats=stats,
        )

    @broker.subscriber("report.appointments")
    @broker.publisher("audit.log.reporting")
    async def report_appointments(
        msg: DateRangeRequest,
    ) -> AppointmentReportResponse:
        _log.info("Generating appointment report")
        stats = await ReportingService.get_appointment_stats(
            msg.start_date, msg.end_date
        )

        await broker.publish(
            AuditLog(
                action="READ",
                resource_type="reports",
                service_name=settings.SERVICE_NAME,
                user_id=msg.user_id,
                metadata={"report": "appointments"},
            ),
            subject="audit.log.reporting",
        )

        return AppointmentReportResponse(stats=stats)

    @broker.subscriber("report.patients")
    @broker.publisher("audit.log.reporting")
    async def report_patients(
        msg: DateRangeRequest,
    ) -> PatientReportResponse:
        _log.info("Generating patient report")
        stats = await ReportingService.get_patient_stats(msg.start_date, msg.end_date)

        await broker.publish(
            AuditLog(
                action="READ",
                resource_type="reports",
                service_name=settings.SERVICE_NAME,
                user_id=msg.user_id,
                metadata={"report": "patients"},
            ),
            subject="audit.log.reporting",
        )

        return PatientReportResponse(stats=stats)
