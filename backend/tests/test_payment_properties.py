"""
Property-based tests for PaymentService.

Property 5 (Req 7.3): Payment Safety Invariant —
    payment_status = "ready_for_payment" MUST imply that deal.status is
    "verified" or "completed". Payment must never be triggered for a deal
    that has not been verified.

Uses hypothesis; no real database required — PaymentService is tested via
mocked DB and DealService.
"""

import sys
import types
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Stub motor so the module loads without a real MongoDB
# ---------------------------------------------------------------------------

def _stub_motor():
    if "motor" not in sys.modules:
        motor_mod = types.ModuleType("motor")
        motor_async_mod = types.ModuleType("motor.motor_asyncio")
        motor_async_mod.AsyncIOMotorClient = MagicMock
        motor_async_mod.AsyncIOMotorDatabase = MagicMock
        motor_mod.motor_asyncio = motor_async_mod
        sys.modules["motor"] = motor_mod
        sys.modules["motor.motor_asyncio"] = motor_async_mod


_stub_motor()

from app.models.deal import Deal, DealStatus, PaymentStatus
from app.services.payment_service import (
    PaymentService,
    InvalidPaymentTriggerError,
    PAYMENT_ELIGIBLE_STATUSES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


def _make_deal(status: DealStatus, deal_id: str = "507f1f77bcf86cd799439011") -> Deal:
    now = datetime.now(timezone.utc)
    return Deal(
        _id=deal_id,
        business_id="biz_001",
        creator_id="creator_001",
        offer_amount=500.0,
        deliverables="1 Instagram Reel",
        deadline=now + timedelta(days=30),
        status=status,
        created_at=now,
        updated_at=now,
    )


def _make_payment_service(deal: Deal) -> PaymentService:
    """Build a PaymentService with a mocked DB that returns the given deal."""
    db_mock = MagicMock()

    # Mock deals collection: find_one returns the deal doc
    deal_doc = deal.model_dump(by_alias=True)
    deal_doc["_id"] = deal.id  # ensure string id

    deals_col = MagicMock()
    deals_col.find_one = AsyncMock(return_value=deal_doc)
    deals_col.update_one = AsyncMock(return_value=None)

    # Mock payments collection: insert_one returns a fake inserted_id
    from bson import ObjectId
    payments_col = MagicMock()
    fake_result = MagicMock()
    fake_result.inserted_id = ObjectId()
    payments_col.insert_one = AsyncMock(return_value=fake_result)
    payments_col.find_one = AsyncMock(return_value=None)

    def _get_col(name):
        if name == "deals":
            return deals_col
        if name == "payments":
            return payments_col
        return MagicMock()

    db_mock.__getitem__ = MagicMock(side_effect=_get_col)

    return PaymentService(db_mock)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

all_statuses = st.sampled_from(list(DealStatus))

# Statuses that are NOT eligible for payment
non_eligible_statuses = st.sampled_from(
    [s for s in DealStatus if s not in PAYMENT_ELIGIBLE_STATUSES]
)

# Positive offer amounts
positive_amount = st.floats(
    min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
)


# ---------------------------------------------------------------------------
# Property 5: Payment Safety Invariant
# payment_status = ready_for_payment ONLY when deal.status is verified or completed
# Validates: Requirements 7.3
# ---------------------------------------------------------------------------

@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status=non_eligible_statuses, amount=positive_amount)
def test_payment_trigger_rejected_for_non_verified_deal(status, amount):
    """
    Property 5: For any Deal NOT in 'verified' or 'completed' status,
    trigger_payment_ready MUST raise InvalidPaymentTriggerError.

    This ensures payment_status = 'ready_for_payment' can never be set
    for a deal that has not been verified.

    **Validates: Requirements 7.3**
    """
    deal = _make_deal(status)
    service = _make_payment_service(deal)

    with pytest.raises(InvalidPaymentTriggerError) as exc_info:
        _run(service.trigger_payment_ready(deal.id, amount))

    assert exc_info.value.current_status == status, (
        f"Expected current_status={status}, got {exc_info.value.current_status}"
    )
    assert status not in PAYMENT_ELIGIBLE_STATUSES, (
        f"Status {status} should not be in PAYMENT_ELIGIBLE_STATUSES"
    )


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(amount=positive_amount)
def test_payment_trigger_succeeds_for_verified_deal(amount):
    """
    Property 5 (positive case): For a Deal in 'verified' status,
    trigger_payment_ready MUST succeed and return a PaymentRecord with
    status = 'ready_for_payment' and a non-empty blockchain_tx_hash.

    **Validates: Requirements 7.2, 7.3**
    """
    deal = _make_deal(DealStatus.verified)
    service = _make_payment_service(deal)

    record = _run(service.trigger_payment_ready(deal.id, amount))

    assert record.status == PaymentStatus.ready_for_payment, (
        f"Expected status=ready_for_payment, got {record.status}"
    )
    assert record.blockchain_tx_hash is not None, "blockchain_tx_hash must not be None"
    assert record.blockchain_tx_hash.startswith("0x"), (
        f"blockchain_tx_hash must start with '0x', got {record.blockchain_tx_hash}"
    )
    assert len(record.blockchain_tx_hash) > 2, "blockchain_tx_hash must be non-empty after '0x'"
    assert record.deal_id == deal.id, (
        f"Expected deal_id={deal.id}, got {record.deal_id}"
    )
    assert record.amount == amount, (
        f"Expected amount={amount}, got {record.amount}"
    )


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(amount=positive_amount)
def test_payment_trigger_succeeds_for_completed_deal(amount):
    """
    Property 5 (completed status): For a Deal in 'completed' status,
    trigger_payment_ready MUST also succeed (completed is a post-verified state).

    **Validates: Requirements 7.3**
    """
    deal = _make_deal(DealStatus.completed)
    service = _make_payment_service(deal)

    record = _run(service.trigger_payment_ready(deal.id, amount))

    assert record.status == PaymentStatus.ready_for_payment, (
        f"Expected status=ready_for_payment for completed deal, got {record.status}"
    )


@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status=all_statuses, amount=positive_amount)
def test_payment_safety_invariant(status, amount):
    """
    Property 5 (full invariant): For ANY deal status, if trigger_payment_ready
    succeeds, then the deal status MUST be in PAYMENT_ELIGIBLE_STATUSES
    (verified or completed). If the deal is not eligible, it MUST raise
    InvalidPaymentTriggerError.

    This is the core safety invariant: payment_status = 'ready_for_payment'
    implies deal.status is 'verified' or 'completed'.

    **Validates: Requirements 7.3**
    """
    deal = _make_deal(status)
    service = _make_payment_service(deal)

    if status in PAYMENT_ELIGIBLE_STATUSES:
        # Must succeed
        record = _run(service.trigger_payment_ready(deal.id, amount))
        assert record.status == PaymentStatus.ready_for_payment, (
            f"Payment record status must be ready_for_payment for eligible deal status={status}"
        )
    else:
        # Must raise
        with pytest.raises(InvalidPaymentTriggerError):
            _run(service.trigger_payment_ready(deal.id, amount))


# ---------------------------------------------------------------------------
# Unit tests for specific requirements
# ---------------------------------------------------------------------------

def test_blockchain_tx_hash_format():
    """Req 7.2: blockchain_tx_hash must be '0x' + hex string."""
    deal = _make_deal(DealStatus.verified)
    service = _make_payment_service(deal)

    record = _run(service.trigger_payment_ready(deal.id, 500.0))

    assert record.blockchain_tx_hash is not None
    assert record.blockchain_tx_hash.startswith("0x")
    # uuid4().hex is 32 hex chars → total length = 34
    hex_part = record.blockchain_tx_hash[2:]
    assert len(hex_part) == 32, f"Expected 32 hex chars, got {len(hex_part)}"
    assert all(c in "0123456789abcdef" for c in hex_part), (
        f"blockchain_tx_hash contains non-hex chars: {hex_part}"
    )


def test_payment_record_has_triggered_at():
    """Req 7.2: PaymentRecord must have a triggered_at timestamp."""
    deal = _make_deal(DealStatus.verified)
    service = _make_payment_service(deal)

    before = datetime.now(timezone.utc)
    record = _run(service.trigger_payment_ready(deal.id, 100.0))
    after = datetime.now(timezone.utc)

    assert record.triggered_at is not None
    assert before <= record.triggered_at <= after, (
        f"triggered_at={record.triggered_at} not in expected range [{before}, {after}]"
    )


def test_invalid_trigger_error_contains_status():
    """Req 7.5: InvalidPaymentTriggerError must contain the current deal status."""
    deal = _make_deal(DealStatus.pending)
    service = _make_payment_service(deal)

    with pytest.raises(InvalidPaymentTriggerError) as exc_info:
        _run(service.trigger_payment_ready(deal.id, 500.0))

    assert exc_info.value.current_status == DealStatus.pending
    assert exc_info.value.deal_id == deal.id


def test_payment_eligible_statuses_are_post_verification():
    """Req 7.3: PAYMENT_ELIGIBLE_STATUSES must only contain verified and completed."""
    assert DealStatus.verified in PAYMENT_ELIGIBLE_STATUSES
    assert DealStatus.completed in PAYMENT_ELIGIBLE_STATUSES
    # No pre-verification statuses should be eligible
    pre_verification = {
        DealStatus.pending,
        DealStatus.accepted,
        DealStatus.rejected,
        DealStatus.countered,
        DealStatus.content_submitted,
        DealStatus.revision_requested,
    }
    assert pre_verification.isdisjoint(PAYMENT_ELIGIBLE_STATUSES), (
        "Pre-verification statuses must not be in PAYMENT_ELIGIBLE_STATUSES"
    )
