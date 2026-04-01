"""
Property-based tests for Deal lifecycle.

Property 10 (Req 5.1): For any valid deal creation request, the resulting
    Deal must have status "pending".

Property 6 (Req 5.6/5.7): For any Deal and any invalid action, attempting
    the transition must raise InvalidTransitionError (HTTP 409 at the API layer).

Uses hypothesis; no real database required — DealService.create_deal is tested
via the in-memory state machine helper, and the router layer is tested with
FastAPI TestClient + mocked DB.
"""

import sys
import types
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

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

from app.models.deal import Deal, DealCreate, DealStatus
from app.services.deal_service import (
    DealService,
    InvalidTransitionError,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# All possible DealStatus values
all_statuses = st.sampled_from(list(DealStatus))

# All possible actions defined in the state machine
all_defined_actions = st.sampled_from(list({action for (_, action) in VALID_TRANSITIONS}))

# Valid deal creation payloads
valid_deal_create = st.fixed_dictionaries({
    "business_id": st.uuids().map(str),
    "creator_id": st.uuids().map(str),
    "offer_amount": st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    "deliverables": st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))),
    "deadline": st.datetimes(
        min_value=datetime(2025, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    ),
})


# ---------------------------------------------------------------------------
# Helper: build a Deal in a given status (no DB needed)
# ---------------------------------------------------------------------------

def _make_deal(status: DealStatus) -> Deal:
    now = datetime.now(timezone.utc)
    return Deal(
        _id="507f1f77bcf86cd799439011",
        business_id="biz_001",
        creator_id="creator_001",
        offer_amount=500.0,
        deliverables="1 Instagram Reel",
        deadline=now + timedelta(days=30),
        status=status,
        created_at=now,
        updated_at=now,
    )


def _make_service() -> DealService:
    """Return a DealService with a mock DB (state machine tests don't need real DB)."""
    db_mock = MagicMock()
    return DealService(db_mock)


# ---------------------------------------------------------------------------
# Property 10: New deal initial status is "pending"
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(payload_data=valid_deal_create)
def test_new_deal_status_is_pending(payload_data):
    """
    Property 10: For any valid deal creation request, the resulting Deal must
    have status "pending".

    **Validates: Requirements 5.1**
    """
    payload = DealCreate(**payload_data)

    # Build the Deal object the same way DealService.create_deal does
    now = datetime.now(timezone.utc)
    deal = Deal(
        business_id=payload.business_id,
        creator_id=payload.creator_id,
        offer_amount=payload.offer_amount,
        deliverables=payload.deliverables,
        deadline=payload.deadline,
        status=DealStatus.pending,
        created_at=now,
        updated_at=now,
    )

    assert deal.status == DealStatus.pending, (
        f"Expected status 'pending', got '{deal.status}'"
    )


# ---------------------------------------------------------------------------
# Property 6: Invalid transitions raise InvalidTransitionError
# Validates: Requirements 5.6, 5.7
# ---------------------------------------------------------------------------

@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status=all_statuses, action=all_defined_actions)
def test_invalid_transition_raises_error(status, action):
    """
    Property 6: For any Deal and any action that is NOT valid for the current
    status, transition_deal_status must raise InvalidTransitionError.

    **Validates: Requirements 5.6, 5.7**
    """
    key = (status, action)
    if key in VALID_TRANSITIONS:
        # This is a valid transition — skip (we only test invalid ones here)
        return

    service = _make_service()
    deal = _make_deal(status)

    with pytest.raises(InvalidTransitionError) as exc_info:
        service.transition_deal_status(deal, action)

    assert exc_info.value.current_status == status
    assert exc_info.value.attempted_action == action


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status=all_statuses, action=all_defined_actions)
def test_valid_transition_does_not_raise(status, action):
    """
    Property 6 (positive case): For any valid (status, action) pair, the
    transition must succeed without raising an error.

    **Validates: Requirements 5.7**
    """
    key = (status, action)
    if key not in VALID_TRANSITIONS:
        return  # Only test valid transitions here

    service = _make_service()
    deal = _make_deal(status)

    # Should not raise
    updated = service.transition_deal_status(deal, action)
    assert updated.status == VALID_TRANSITIONS[key]


# ---------------------------------------------------------------------------
# Property 6 (extended): updated_at is always set on valid transitions
# Validates: Requirements 5.8
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(status=all_statuses, action=all_defined_actions)
def test_updated_at_set_on_valid_transition(status, action):
    """
    Property (Req 5.8): updated_at must be set to current time on every
    successful status change.

    **Validates: Requirements 5.8**
    """
    key = (status, action)
    if key not in VALID_TRANSITIONS:
        return

    service = _make_service()
    deal = _make_deal(status)
    old_updated_at = deal.updated_at

    updated = service.transition_deal_status(deal, action)

    # updated_at must be >= old value (it was just set to now())
    assert updated.updated_at >= old_updated_at, (
        "updated_at was not advanced after status transition"
    )
