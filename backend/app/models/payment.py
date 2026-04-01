from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.models.base import BaseDocument
from app.models.deal import PaymentStatus


class PaymentRecord(BaseDocument):
    deal_id: str
    amount: float
    status: PaymentStatus
    blockchain_tx_hash: Optional[str] = None
    triggered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class PaymentResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    deal_id: str
    amount: float
    status: PaymentStatus
    blockchain_tx_hash: Optional[str] = None
    triggered_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
    }
