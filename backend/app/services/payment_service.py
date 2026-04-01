"""
PaymentService — manages payment state transitions (blockchain-ready mock).
"""

import uuid
from datetime import datetime, timezone

from app.models.deal import DealStatus, PaymentStatus
from app.models.payment import PaymentRecord
from app.services.deal_service import DealNotFoundError, DealService


class PaymentNotFoundError(Exception):
    pass


class InvalidPaymentTriggerError(Exception):
    def __init__(self, deal_id: str, current_status: str):
        self.deal_id = deal_id
        self.current_status = current_status
        super().__init__(
            f"Cannot trigger payment for deal '{deal_id}' in status '{current_status}'. "
            "Deal must be in 'verified' status."
        )


PAYMENT_ELIGIBLE_STATUSES = {DealStatus.verified, DealStatus.completed}


class PaymentService:
    def __init__(self, db) -> None:
        self._db = db
        self._col = db["payments"]
        self._deal_service = DealService(db)

    async def trigger_payment_ready(self, deal_id: str, amount: float) -> PaymentRecord:
        deal = await self._deal_service.get_deal(deal_id)
        if deal.status not in PAYMENT_ELIGIBLE_STATUSES:
            raise InvalidPaymentTriggerError(deal_id, deal.status)

        blockchain_tx_hash = "0x" + uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        payment_id = uuid.uuid4().hex

        record = PaymentRecord(
            _id=payment_id,
            deal_id=deal_id,
            amount=amount,
            status=PaymentStatus.ready_for_payment,
            blockchain_tx_hash=blockchain_tx_hash,
            triggered_at=now,
            created_at=now,
            updated_at=now,
        )

        doc = record.model_dump(by_alias=True)
        await self._col.insert_one(doc)

        await self._db["deals"].update_one(
            {"_id": deal_id},
            {"$set": {"payment_status": PaymentStatus.ready_for_payment, "updated_at": now}},
        )

        return record

    async def get_payment_status(self, deal_id: str) -> PaymentRecord:
        doc = await self._col.find_one({"deal_id": deal_id})
        if doc is None:
            raise PaymentNotFoundError(f"No payment record found for deal '{deal_id}'")
        return PaymentRecord(**doc)
