from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.base import BaseDocument


class DealStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    countered = "countered"
    content_submitted = "content_submitted"
    verified = "verified"
    revision_requested = "revision_requested"
    completed = "completed"


class PaymentStatus(str, Enum):
    not_triggered = "not_triggered"
    ready_for_payment = "ready_for_payment"
    processing = "processing"
    paid = "paid"


class CounterOffer(BaseModel):
    """Represents a single counter offer in negotiation history."""
    author: str  # "creator" or "business"
    message: Optional[str] = None
    proposed_amount: Optional[float] = None
    proposed_deliverables: Optional[str] = None
    timestamp: datetime

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        if v not in ("creator", "business"):
            raise ValueError("author must be 'creator' or 'business'")
        return v

    @field_validator("proposed_amount")
    @classmethod
    def validate_proposed_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("proposed_amount must be positive")
        return v


class Deal(BaseDocument):
    business_id: str
    creator_id: str
    offer_amount: float
    deliverables: str
    deadline: datetime
    status: DealStatus = DealStatus.pending
    ad_idea: Optional[str] = None
    content_url: Optional[str] = None
    verification_score: Optional[float] = None
    payment_status: PaymentStatus = PaymentStatus.not_triggered
    
    # Counter negotiation fields
    counter_message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None
    counter_history: list[CounterOffer] = []

    @field_validator("counter_amount")
    @classmethod
    def validate_counter_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("counter_amount must be positive")
        return v


class DealCreate(BaseModel):
    business_id: str
    creator_id: str
    offer_amount: float
    deliverables: str
    deadline: datetime

    @field_validator("offer_amount")
    @classmethod
    def validate_offer_amount(cls, v: float) -> float:
        from app.core.config import settings

        if v <= 0:
            raise ValueError("offer_amount must be positive (greater than 0)")
        if v > settings.MAX_OFFER_AMOUNT:
            raise ValueError(
                f"offer_amount {v} exceeds the maximum allowed value of {settings.MAX_OFFER_AMOUNT}"
            )
        return v


class DealResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    business_id: str
    creator_id: str
    offer_amount: float
    deliverables: str
    deadline: datetime
    status: DealStatus
    ad_idea: Optional[str] = None
    content_url: Optional[str] = None
    verification_score: Optional[float] = None
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    
    # Counter negotiation fields
    counter_message: Optional[str] = None
    counter_amount: Optional[float] = None
    counter_deliverables: Optional[str] = None
    counter_history: list[CounterOffer] = []

    model_config = {
        "populate_by_name": True,
    }
