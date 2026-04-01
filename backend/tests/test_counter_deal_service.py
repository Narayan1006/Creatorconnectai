"""
Test counter_deal service method implementation.
Task 3.1: Add counter_deal method to DealService
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.deal import Deal, DealCreate, DealStatus, CounterOffer
from app.services.deal_service import DealService, InvalidTransitionError, DealNotFoundError


@pytest.fixture
async def db_fixture(integration_client):
    """Extract database from integration_client fixture."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    return db


@pytest.mark.asyncio
async def test_counter_deal_with_all_fields(integration_client):
    """Test counter_deal with message, amount, and deliverables."""
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
    
    # Counter the deal
    countered = await service.counter_deal(
        deal.id,
        message="I'd like to negotiate",
        counter_amount=1500.0,
        counter_deliverables="Modified deliverables"
    )
    
    # Verify status transition
    assert countered.status == DealStatus.countered
    
    # Verify counter fields are stored
    assert countered.counter_message == "I'd like to negotiate"
    assert countered.counter_amount == 1500.0
    assert countered.counter_deliverables == "Modified deliverables"
    
    # Verify original offer is preserved (Requirement 1.7)
    assert countered.offer_amount == 1000.0
    assert countered.deliverables == "Original deliverables"
    
    # Verify timestamp updated (Requirement 1.8)
    assert countered.updated_at > countered.created_at
    
    # Verify counter_history has one entry
    assert len(countered.counter_history) == 1
    assert countered.counter_history[0].author == "creator"
    assert countered.counter_history[0].message == "I'd like to negotiate"
    assert countered.counter_history[0].proposed_amount == 1500.0
    assert countered.counter_history[0].proposed_deliverables == "Modified deliverables"


@pytest.mark.asyncio
async def test_counter_deal_with_only_message(integration_client):
    """Test counter_deal with only message."""
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
    
    # Counter with only message
    countered = await service.counter_deal(
        deal.id,
        message="Can we discuss this?"
    )
    
    assert countered.status == DealStatus.countered
    assert countered.counter_message == "Can we discuss this?"
    assert countered.counter_amount is None
    assert countered.counter_deliverables is None
    assert len(countered.counter_history) == 1


@pytest.mark.asyncio
async def test_counter_deal_with_only_amount(integration_client):
    """Test counter_deal with only amount."""
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
    
    # Counter with only amount
    countered = await service.counter_deal(
        deal.id,
        counter_amount=1200.0
    )
    
    assert countered.status == DealStatus.countered
    assert countered.counter_message is None
    assert countered.counter_amount == 1200.0
    assert countered.counter_deliverables is None
    assert len(countered.counter_history) == 1


@pytest.mark.asyncio
async def test_counter_deal_with_no_fields(integration_client):
    """Test counter_deal with no optional fields."""
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
    
    # Counter with no fields
    countered = await service.counter_deal(deal.id)
    
    assert countered.status == DealStatus.countered
    assert countered.counter_message is None
    assert countered.counter_amount is None
    assert countered.counter_deliverables is None
    assert len(countered.counter_history) == 1


@pytest.mark.asyncio
async def test_counter_deal_invalid_status(integration_client):
    """Test counter_deal fails on non-pending deal."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Create and accept a deal
    payload = DealCreate(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="Original deliverables",
        deadline=datetime.now(timezone.utc) + timedelta(days=30)
    )
    deal = await service.create_deal(payload, ad_idea="Test ad idea")
    await service.accept_deal(deal.id)
    
    # Try to counter an accepted deal
    with pytest.raises(InvalidTransitionError) as exc_info:
        await service.counter_deal(deal.id, message="Too late")
    
    assert exc_info.value.current_status == DealStatus.accepted
    assert exc_info.value.attempted_action == "COUNTER"


@pytest.mark.asyncio
async def test_counter_deal_not_found(integration_client):
    """Test counter_deal fails on non-existent deal."""
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    with pytest.raises(DealNotFoundError):
        await service.counter_deal("nonexistent_id", message="Hello")


@pytest.mark.asyncio
async def test_counter_deal_persists_to_database(integration_client):
    """Test counter_deal persists data to database."""
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
    
    # Counter the deal
    await service.counter_deal(
        deal.id,
        message="Let's negotiate",
        counter_amount=1300.0
    )
    
    # Retrieve the deal from database
    retrieved = await service.get_deal(deal.id)
    
    # Verify data persisted
    assert retrieved.status == DealStatus.countered
    assert retrieved.counter_message == "Let's negotiate"
    assert retrieved.counter_amount == 1300.0
    assert len(retrieved.counter_history) == 1
    assert retrieved.counter_history[0].author == "creator"
