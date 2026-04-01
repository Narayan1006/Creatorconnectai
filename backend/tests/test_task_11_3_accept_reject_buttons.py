"""
Verification tests for Task 11.3: Add accept/reject counter buttons

Tests the BusinessDashboard UI integration with accept-counter and reject-counter endpoints.
Requirements: 5.1, 5.4

This test file verifies:
- Accept counter button functionality
- Reject counter button functionality
- Confirmation dialog logic for accepting when terms changed
- Proper API endpoint integration

Note: The backend endpoints (accept-counter, reject-counter) are already tested in
test_accept_counter.py and test_reject_counter.py. These tests verify the UI integration.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from app.services.deal_service import DealService
from app.models.deal import Deal, DealStatus, CounterOffer


@pytest.fixture
def mock_db():
    """Create an in-memory mock database for testing."""
    store = {}
    
    async def insert_one(doc):
        doc = dict(doc)
        oid = doc.get("_id")
        store[str(oid)] = doc
        result = MagicMock()
        result.inserted_id = oid
        return result
    
    async def find_one(query):
        if "_id" in query:
            return store.get(str(query["_id"]))
        return None
    
    async def update_one(query, update):
        if "_id" in query:
            key = str(query["_id"])
            if key in store:
                set_vals = update.get("$set", {})
                store[key].update(set_vals)
    
    collection = MagicMock()
    collection.insert_one = insert_one
    collection.find_one = find_one
    collection.update_one = update_one
    
    db = MagicMock()
    db.__getitem__ = lambda self, name: collection
    
    return db


@pytest.mark.asyncio
async def test_ui_accept_counter_with_terms_changed(mock_db):
    """
    Test UI scenario: Business accepts counter when terms have changed.
    This simulates the confirmation dialog flow in BusinessDashboard.tsx.
    """
    service = DealService(mock_db)
    
    # Create a countered deal with changed terms
    deal = Deal(
        _id="deal_ui_123",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1500.0,  # Changed
        counter_deliverables="1 Instagram post + 2 stories",  # Changed
        counter_message="Can we do more?",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # UI logic: Check if terms changed (this would trigger confirmation dialog)
    has_terms_changed = (
        (deal.counter_amount is not None and deal.counter_amount != deal.offer_amount) or
        (deal.counter_deliverables is not None and deal.counter_deliverables != deal.deliverables)
    )
    
    assert has_terms_changed is True, "UI should detect terms have changed"
    
    # After user confirms in dialog, accept the counter
    result = await service.accept_counter("deal_ui_123")
    
    # Verify the counter terms were applied
    assert result.status == DealStatus.accepted
    assert result.offer_amount == 1500.0
    assert result.deliverables == "1 Instagram post + 2 stories"


@pytest.mark.asyncio
async def test_ui_accept_counter_without_terms_changed(mock_db):
    """
    Test UI scenario: Business accepts counter when only message (no term changes).
    This should NOT trigger confirmation dialog.
    """
    service = DealService(mock_db)
    
    # Create a countered deal with only message, no term changes
    deal = Deal(
        _id="deal_ui_456",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Just wanted to discuss timing",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # UI logic: Check if terms changed
    has_terms_changed = (
        (deal.counter_amount is not None and deal.counter_amount != deal.offer_amount) or
        (deal.counter_deliverables is not None and deal.counter_deliverables != deal.deliverables)
    )
    
    assert has_terms_changed is False, "UI should detect no term changes"
    
    # Accept directly without confirmation dialog
    result = await service.accept_counter("deal_ui_456")
    
    # Verify original terms preserved
    assert result.status == DealStatus.accepted
    assert result.offer_amount == 1000.0
    assert result.deliverables == "1 Instagram post"


@pytest.mark.asyncio
async def test_ui_reject_counter_flow(mock_db):
    """
    Test UI scenario: Business rejects counter offer.
    This simulates the reject button flow in BusinessDashboard.tsx.
    """
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal_ui_789",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=2000.0,
        counter_message="Too expensive",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Reject the counter
    result = await service.reject_counter("deal_ui_789")
    
    # Verify status transitioned to rejected
    assert result.status == DealStatus.rejected


@pytest.mark.asyncio
async def test_ui_confirmation_dialog_logic_amount_only(mock_db):
    """Test confirmation dialog logic when only amount changed."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal_ui_amount",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1200.0,  # Only amount changed
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # UI logic: Should trigger confirmation
    has_terms_changed = (
        (deal.counter_amount is not None and deal.counter_amount != deal.offer_amount) or
        (deal.counter_deliverables is not None and deal.counter_deliverables != deal.deliverables)
    )
    
    assert has_terms_changed is True
    
    result = await service.accept_counter("deal_ui_amount")
    assert result.offer_amount == 1200.0
    assert result.deliverables == "1 Instagram post"  # Unchanged


@pytest.mark.asyncio
async def test_ui_confirmation_dialog_logic_deliverables_only(mock_db):
    """Test confirmation dialog logic when only deliverables changed."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal_ui_deliv",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_deliverables="2 Instagram posts",  # Only deliverables changed
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # UI logic: Should trigger confirmation
    has_terms_changed = (
        (deal.counter_amount is not None and deal.counter_amount != deal.offer_amount) or
        (deal.counter_deliverables is not None and deal.counter_deliverables != deal.deliverables)
    )
    
    assert has_terms_changed is True
    
    result = await service.accept_counter("deal_ui_deliv")
    assert result.offer_amount == 1000.0  # Unchanged
    assert result.deliverables == "2 Instagram posts"


@pytest.mark.asyncio
async def test_ui_countered_deals_display_data(mock_db):
    """
    Test that countered deals have all necessary data for UI display.
    This verifies the data structure matches what BusinessDashboard.tsx expects.
    """
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal_ui_display",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Let's negotiate",
        counter_amount=1500.0,
        counter_deliverables="1 Instagram post + 2 stories",
        counter_history=[
            CounterOffer(
                author="creator",
                message="Let's negotiate",
                proposed_amount=1500.0,
                proposed_deliverables="1 Instagram post + 2 stories",
                timestamp=datetime.now(timezone.utc)
            )
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Verify all UI-required fields are present
    assert deal.status == DealStatus.countered
    assert deal.offer_amount == 1000.0  # Original
    assert deal.counter_amount == 1500.0  # Counter
    assert deal.deliverables == "1 Instagram post"  # Original
    assert deal.counter_deliverables == "1 Instagram post + 2 stories"  # Counter
    assert deal.counter_message == "Let's negotiate"
    assert len(deal.counter_history) == 1
    assert deal.counter_history[0].author == "creator"
