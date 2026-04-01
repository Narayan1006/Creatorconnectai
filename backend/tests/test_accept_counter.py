"""
Unit tests for accept_counter method in DealService.

Tests Task 6.1: Add accept_counter method to DealService
Requirements: 5.1, 5.2, 5.3, 4.6
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from bson import ObjectId
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
async def test_accept_counter_transitions_to_accepted(mock_db):
    """Test that accepting a countered deal transitions status to accepted."""
    service = DealService(mock_db)
    
    # Create a countered deal
    deal = Deal(
        _id="deal123",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Can we do 1500?",
        counter_amount=1500.0,
        counter_deliverables="Modified deliverables",
        counter_history=[
            CounterOffer(
                author="creator",
                message="Can we do 1500?",
                proposed_amount=1500.0,
                proposed_deliverables="Modified deliverables",
                timestamp=datetime.now(timezone.utc)
            )
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Insert the deal
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Accept the counter
    result = await service.accept_counter("deal123")
    
    # Verify status transitioned to accepted
    assert result.status == DealStatus.accepted
    assert result.updated_at > deal.updated_at


@pytest.mark.asyncio
async def test_accept_counter_applies_counter_amount(mock_db):
    """Test that accepting counter applies counter_amount to offer_amount."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal456",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1500.0,
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    result = await service.accept_counter("deal456")
    
    # Verify offer_amount was updated to counter_amount
    assert result.offer_amount == 1500.0


@pytest.mark.asyncio
async def test_accept_counter_applies_counter_deliverables(mock_db):
    """Test that accepting counter applies counter_deliverables to deliverables."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal789",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_deliverables="Modified deliverables",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    result = await service.accept_counter("deal789")
    
    # Verify deliverables was updated to counter_deliverables
    assert result.deliverables == "Modified deliverables"


@pytest.mark.asyncio
async def test_accept_counter_applies_both_terms(mock_db):
    """Test that accepting counter applies both counter_amount and counter_deliverables."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal101",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=2000.0,
        counter_deliverables="New deliverables",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    result = await service.accept_counter("deal101")
    
    # Verify both fields were updated
    assert result.offer_amount == 2000.0
    assert result.deliverables == "New deliverables"


@pytest.mark.asyncio
async def test_accept_counter_preserves_counter_history(mock_db):
    """Test that accepting counter preserves counter_history."""
    service = DealService(mock_db)
    
    counter_history = [
        CounterOffer(
            author="creator",
            message="First counter",
            proposed_amount=1500.0,
            proposed_deliverables="First deliverables",
            timestamp=datetime.now(timezone.utc)
        ),
        CounterOffer(
            author="business",
            message="Business counter",
            proposed_amount=1300.0,
            proposed_deliverables="Business deliverables",
            timestamp=datetime.now(timezone.utc)
        )
    ]
    
    deal = Deal(
        _id="deal202",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1300.0,
        counter_history=counter_history,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    result = await service.accept_counter("deal202")
    
    # Verify counter_history is preserved
    assert len(result.counter_history) == 2
    assert result.counter_history[0].author == "creator"
    assert result.counter_history[1].author == "business"


@pytest.mark.asyncio
async def test_accept_counter_without_counter_terms(mock_db):
    """Test that accepting counter without counter terms keeps original values."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal303",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Just a message, no terms",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    result = await service.accept_counter("deal303")
    
    # Verify original values are preserved when no counter terms provided
    assert result.offer_amount == 1000.0
    assert result.deliverables == "Original deliverables"
    assert result.status == DealStatus.accepted


@pytest.mark.asyncio
async def test_accept_counter_rejects_pending_deal(mock_db):
    """Test that accepting counter on pending deal raises InvalidTransitionError."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal404",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.pending,
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    # Attempt to accept counter on pending deal should fail
    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.accept_counter("deal404")
    
    assert exc_info.value.current_status == DealStatus.pending
    assert exc_info.value.attempted_action == "ACCEPT_COUNTER"


@pytest.mark.asyncio
async def test_accept_counter_persists_to_database(mock_db):
    """Test that accept_counter persists changes to database."""
    service = DealService(mock_db)
    
    deal = Deal(
        _id="deal505",
        business_id="biz1",
        creator_id="creator1",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1800.0,
        counter_deliverables="Updated deliverables",
        counter_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_db["deals"].insert_one(deal.model_dump(by_alias=True))
    
    await service.accept_counter("deal505")
    
    # Retrieve from database and verify persistence
    persisted = await mock_db["deals"].find_one({"_id": "deal505"})
    assert persisted["status"] == DealStatus.accepted
    assert persisted["offer_amount"] == 1800.0
    assert persisted["deliverables"] == "Updated deliverables"
