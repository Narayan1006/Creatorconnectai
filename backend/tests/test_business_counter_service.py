"""
Test business_counter service method implementation.
Task 7.1: Add business_counter method to DealService
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.deal import Deal, DealCreate, DealStatus, CounterOffer
from app.services.deal_service import DealService, InvalidTransitionError, DealNotFoundError


@pytest.mark.asyncio
async def test_business_counter_with_all_fields(integration_client):
    """Test business_counter with message, amount, and deliverables."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create a pending deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    
    # Creator counters the deal
    countered = await service.counter_deal(
        deal.id,
        message="I'd like $1500",
        counter_amount=1500.0,
        counter_deliverables="Modified deliverables"
    )
    
    # Business counters back
    business_countered = await service.business_counter(
        countered.id,
        message="How about $1300?",
        counter_amount=1300.0,
        counter_deliverables="Slightly modified deliverables"
    )
    
    # Verify status remains countered (Requirement 6.1)
    assert business_countered.status == DealStatus.countered
    
    # Verify business counter fields are stored (Requirement 6.2)
    assert business_countered.counter_message == "How about $1300?"
    assert business_countered.counter_amount == 1300.0
    assert business_countered.counter_deliverables == "Slightly modified deliverables"
    
    # Verify original offer is still preserved
    assert business_countered.offer_amount == 1000.0
    assert business_countered.deliverables == "Original deliverables"
    
    # Verify timestamp updated
    assert business_countered.updated_at > countered.updated_at
    
    # Verify counter_history has two entries (Requirement 6.3, 6.4)
    assert len(business_countered.counter_history) == 2
    assert business_countered.counter_history[0].author == "creator"
    assert business_countered.counter_history[0].message == "I'd like $1500"
    assert business_countered.counter_history[1].author == "business"
    assert business_countered.counter_history[1].message == "How about $1300?"
    assert business_countered.counter_history[1].proposed_amount == 1300.0


@pytest.mark.asyncio
async def test_business_counter_with_only_message(integration_client):
    """Test business_counter with only message."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create and counter a deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    countered = await service.counter_deal(deal.id, message="Counter message")
    
    # Business counters with only message
    business_countered = await service.business_counter(
        countered.id,
        message="Let's discuss this further"
    )
    
    assert business_countered.status == DealStatus.countered
    assert business_countered.counter_message == "Let's discuss this further"
    assert business_countered.counter_amount is None
    assert business_countered.counter_deliverables is None
    assert len(business_countered.counter_history) == 2


@pytest.mark.asyncio
async def test_business_counter_with_only_amount(integration_client):
    """Test business_counter with only amount."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create and counter a deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    countered = await service.counter_deal(deal.id, counter_amount=1500.0)
    
    # Business counters with only amount
    business_countered = await service.business_counter(
        countered.id,
        counter_amount=1200.0
    )
    
    assert business_countered.status == DealStatus.countered
    assert business_countered.counter_message is None
    assert business_countered.counter_amount == 1200.0
    assert business_countered.counter_deliverables is None
    assert len(business_countered.counter_history) == 2


@pytest.mark.asyncio
async def test_business_counter_invalid_status(integration_client):
    """Test business_counter fails on non-countered deal."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create a pending deal (not countered)
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    
    # Try to business_counter a pending deal
    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.business_counter(deal.id, message="Can't counter pending")
    
    assert exc_info.value.current_status == DealStatus.pending
    assert exc_info.value.attempted_action == "BUSINESS_COUNTER"


@pytest.mark.asyncio
async def test_business_counter_not_found(integration_client):
    """Test business_counter fails on non-existent deal."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    with pytest.raises(DealNotFoundError):
        await service.business_counter("nonexistent_id", message="Hello")


@pytest.mark.asyncio
async def test_business_counter_persists_to_database(integration_client):
    """Test business_counter persists data to database."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create and counter a deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    countered = await service.counter_deal(
        deal.id,
        message="Creator counter",
        counter_amount=1500.0
    )
    
    # Business counters
    await service.business_counter(
        countered.id,
        message="Business counter",
        counter_amount=1300.0
    )
    
    # Retrieve the deal from database
    retrieved = await service.get_deal(countered.id)
    
    # Verify data persisted
    assert retrieved.status == DealStatus.countered
    assert retrieved.counter_message == "Business counter"
    assert retrieved.counter_amount == 1300.0
    assert len(retrieved.counter_history) == 2
    assert retrieved.counter_history[0].author == "creator"
    assert retrieved.counter_history[1].author == "business"


@pytest.mark.asyncio
async def test_multiple_round_trip_counters(integration_client):
    """Test multiple rounds of creator and business counters (Requirement 6.4)."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create a deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    
    # Round 1: Creator counters
    round1 = await service.counter_deal(
        deal.id,
        message="I want $1500",
        counter_amount=1500.0
    )
    
    # Round 2: Business counters
    round2 = await service.business_counter(
        round1.id,
        message="How about $1200?",
        counter_amount=1200.0
    )
    
    # Round 3: Creator counters again
    round3 = await service.counter_deal(
        round2.id,
        message="Meet me at $1350",
        counter_amount=1350.0
    )
    
    # Round 4: Business counters again
    round4 = await service.business_counter(
        round3.id,
        message="Final offer: $1300",
        counter_amount=1300.0
    )
    
    # Verify all rounds are preserved in counter_history
    assert len(round4.counter_history) == 4
    assert round4.counter_history[0].author == "creator"
    assert round4.counter_history[0].proposed_amount == 1500.0
    assert round4.counter_history[1].author == "business"
    assert round4.counter_history[1].proposed_amount == 1200.0
    assert round4.counter_history[2].author == "creator"
    assert round4.counter_history[2].proposed_amount == 1350.0
    assert round4.counter_history[3].author == "business"
    assert round4.counter_history[3].proposed_amount == 1300.0
    
    # Verify status is still countered
    assert round4.status == DealStatus.countered
    
    # Verify original offer is still preserved
    assert round4.offer_amount == 1000.0
    assert round4.deliverables == "Original deliverables"
