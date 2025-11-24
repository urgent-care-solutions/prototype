import asyncio
import logging
import random

from sqlalchemy import select
from src.config import settings
from src.database import AsyncSessionLocal
from src.models import Transaction

from shared.messages import ChargeCreate, RefundCreate

_log = logging.getLogger(settings.LOGGER)


class BillingService:
    @staticmethod
    async def process_charge(data: ChargeCreate) -> Transaction:
        async with AsyncSessionLocal() as session:
            # 1. Create Pending Transaction
            transaction = Transaction(
                patient_id=str(data.patient_id),
                appointment_id=str(data.appointment_id)
                if data.appointment_id
                else None,
                type="CHARGE",
                amount=data.amount,
                currency=data.currency,
                status="pending",
                description=data.description,
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)

            # 2. Simulate Payment Gateway Latency
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # 3. Simulate Failure
            if random.random() < settings.FAILURE_RATE:
                transaction.status = "failed"
                transaction.error_message = (
                    "Mock Gateway: Insufficient Funds or Network Error"
                )
                await session.commit()
                _log.warning(
                    f"Charge failed for transaction {transaction.id}"
                )
                raise ValueError(transaction.error_message)

            # 4. Success
            transaction.status = "success"
            await session.commit()
            _log.info(
                f"Charge successful: {transaction.id} for amount {transaction.amount}"
            )
            return transaction

    @staticmethod
    async def process_refund(data: RefundCreate) -> Transaction:
        async with AsyncSessionLocal() as session:
            # 1. Check Original Transaction
            stmt = select(Transaction).where(
                Transaction.id == str(data.transaction_id)
            )
            result = await session.execute(stmt)
            original = result.scalars().first()

            if not original:
                raise ValueError("Original transaction not found")

            if (
                original.type != "CHARGE"
                or original.status != "success"
            ):
                raise ValueError(
                    "Cannot refund a failed transaction or another refund"
                )

            # Default to full refund if amount not specified
            refund_amount = (
                data.amount if data.amount else original.amount
            )

            if refund_amount > original.amount:
                raise ValueError(
                    "Refund amount cannot exceed original charge"
                )

            # 2. Create Refund Transaction
            refund_tx = Transaction(
                patient_id=original.patient_id,
                appointment_id=original.appointment_id,
                type="REFUND",
                amount=refund_amount,
                currency=original.currency,
                status="pending",
                reference_id=original.id,
                description=data.reason or "Refund request",
            )
            session.add(refund_tx)
            await session.commit()

            # 3. Simulate Gateway
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # 4. Success (Refunds rarely fail in mock logic unless logic error)
            refund_tx.status = "success"
            await session.commit()
            await session.refresh(refund_tx)

            _log.info(
                f"Refund successful: {refund_tx.id} referencing {original.id}"
            )
            return refund_tx
