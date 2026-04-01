"""
Unit tests for reject_counter method in DealService.

Task 6.2: Add reject_counter method to DealService
Requirements: 5.4
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from app.services.deal_service import DealService, InvalidTransitionError
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
async def test_reject_counter_success(mock_db):
    """Test rejecting a countered deal transitions to rejected status."""
    service = DealService(mock_db)
    
    # Create a countered deal
    deal = Deal(
        _id="test_deal_1",
        business_id="biz_1",
        creator_id="creator_1",
        offer_amount=1000.0,
        deliverables="Test deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Can we do $1500?",
        counter_amount=1500.0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Reject the counter
    result = await service.reject_counter("test_deal_1")
    
    # Verify status transitioned to rejected
    assert result.status == DealStatus.rejected
    assert result.updated_at > deal.updated_at
    
    # Verify original terms are preserved
    assert result.offer_amount == 1000.0
    assert result.deliverables == "Test deliverables"
    
    # Verify counter data is still present
    assert result.counter_message == "Can we do $1500?"
    assert result.counter_amount == 1500.0


@pytest.mark.asyncio
async def test_reject_counter_invalid_status(mock_db):
    """Test rejecting a non-countered deal raises InvalidTransitionError."""
    service = DealService(mock_db)
    
    # Create a pending deal (not countered)
    deal = Deal(
        _id="test_deal_2",
        business_id="biz_1",
        creator_id="creator_1",
        offer_amount=1000.0,
        deliverables="Test deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.pending,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Attempt to reject counter on pending deal should fail
    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.reject_counter("test_deal_2")
    
    assert exc_info.value.current_status == DealStatus.pending
    assert exc_info.value.attempted_action == "REJECT_COUNTER"


@pytest.mark.asyncio
async def test_reject_counter_preserves_counter_history(mock_db):
    """Test rejecting a counter preserves the counter_history."""
    service = DealService(mock_db)
    
    # Create a countered deal with counter history
    counter_history = [
        CounterOffer(
            author="creator",
            message="Can we do $1500?",
            proposed_amount=1500.0,
            timestamp=datetime.now(timezone.utc)
        )
    ]
    
    deal = Deal(
        _id="test_deal_3",
        business_id="biz_1",
        creator_id="creator_1",
        offer_amount=1000.0,
        deliverables="Test deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Can we do $1500?",
        counter_amount=1500.0,
        counter_history=counter_history,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Reject the counter
    result = await service.reject_counter("test_deal_3")
    
    # Verify counter_history is preserved
    assert len(result.counter_history) == 1
    assert result.counter_history[0].author == "creator"
    assert result.counter_history[0].message == "Can we do $1500?"
    assert result.counter_history[0].proposed_amount == 1500.0


@pytest.mark.asyncio
async def test_reject_counter_persists_to_database(mock_db):
    """Test that reject_counter persists changes to database."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="test_deal_4",
        business_id="biz_1",
        creator_id="creator_1",
        offer_amount=1000.0,
        deliverables="Test deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1800.0,
        counter_deliverables="Updated deliverables",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    await service.reject_counter("test_deal_4")
    
    # Retrieve from database and verify persistence
    persisted = await mock_db["deals"].find_one({"_id": "test_deal_4"})
    assert persisted["status"] == DealStatus.rejected
    # Original terms should remain unchanged
    assert persisted["offer_amount"] == 1000.0
    assert persisted["deliverables"] == "Test deliverables"
