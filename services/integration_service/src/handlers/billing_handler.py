import logging

from faststream.nats import NatsBroker
from src.config import settings
from src.services.billing_service import BillingService

from shared.messages import (
    AuditLog,
    ChargeCreate,
    ChargeCreated,
    RefundCreate,
    RefundCreated,
)

_log = logging.getLogger(settings.LOGGER)


def register_handlers(broker: NatsBroker):

    @broker.subscriber("billing.charge")
    @broker.publisher("billing.charged")
    @broker.publisher("audit.log.billing")
    async def handle_charge(msg: ChargeCreate) -> ChargeCreated:
        _log.info(
            f"Processing charge for patient {msg.patient_id}, Amount: {msg.amount}"
        )

        try:
            tx = await BillingService.process_charge(msg)

            # Audit Log
            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="billing",
                    resource_id=tx.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "type": "charge",
                        "amount": tx.amount,
                        "status": "success",
                    },
                ),
                subject="audit.log.billing",
            )

            return ChargeCreated(
                transaction_id=tx.id,
                patient_id=msg.patient_id,
                amount=tx.amount,
                currency=tx.currency,
                status="success",
                success=True,
            )

        except Exception as e:
            _log.error(f"Charge failed: {e}")

            # Audit Log for Failure
            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="billing",
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    success=False,
                    metadata={
                        "type": "charge",
                        "amount": msg.amount,
                        "error": str(e),
                    },
                ),
                subject="audit.log.billing",
            )

            return ChargeCreated(
                transaction_id=msg.message_id,  # Fallback ID if DB creation failed
                patient_id=msg.patient_id,
                amount=msg.amount,
                status="failed",
                success=False,
                error_message=str(e),
            )

    @broker.subscriber("billing.refund")
    @broker.publisher("billing.refunded")
    @broker.publisher("audit.log.billing")
    async def handle_refund(msg: RefundCreate) -> RefundCreated:
        _log.info(
            f"Processing refund for transaction {msg.transaction_id}"
        )

        try:
            tx = await BillingService.process_refund(msg)

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="billing",
                    resource_id=tx.id,
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    metadata={
                        "type": "refund",
                        "original_tx": str(msg.transaction_id),
                        "amount": tx.amount,
                    },
                ),
                subject="audit.log.billing",
            )

            return RefundCreated(
                refund_transaction_id=tx.id,
                original_transaction_id=msg.transaction_id,
                amount=tx.amount,
                success=True,
            )

        except Exception as e:
            _log.error(f"Refund failed: {e}")

            await broker.publish(
                AuditLog(
                    action="CREATE",
                    resource_type="billing",
                    service_name=settings.SERVICE_NAME,
                    user_id=msg.user_id,
                    success=False,
                    metadata={
                        "type": "refund",
                        "original_tx": str(msg.transaction_id),
                        "error": str(e),
                    },
                ),
                subject="audit.log.billing",
            )

            return RefundCreated(
                refund_transaction_id=msg.message_id,
                original_transaction_id=msg.transaction_id,
                amount=0.0,
                success=False,
                error_message=str(e),
            )
