"""
Unit tests for counter_deal edge cases.
Task 3.5: Write unit tests for counter_deal edge cases
Requirements: 1.1, 1.2, 1.3, 1.5, 1.6
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.deal import Deal, DealCreate, DealStatus
from app.services.deal_service import DealService, DealNotFoundError
from app.core.config import settings


@pytest.mark.asyncio
async def test_counter_with_only_message(integration_client):
    """Test counter with only message (no amount or deliverables).
    
    Requirements: 1.1
    """
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
        message="I'd like to discuss the timeline"
    )
    
    # Verify status transition
    assert countered.status == DealStatus.countered
    
    # Verify only message is set
    assert countered.counter_message == "I'd like to discuss the timeline"
    assert countered.counter_amount is None
    assert countered.counter_deliverables is None
    
    # Verify original offer preserved
    assert countered.offer_amount == 1000.0
    assert countered.deliverables == "Original deliverables"
    
    # Verify counter_history
    assert len(countered.counter_history) == 1
    assert countered.counter_history[0].author == "creator"
    assert countered.counter_history[0].message == "I'd like to discuss the timeline"
    assert countered.counter_history[0].proposed_amount is None
    assert countered.counter_history[0].proposed_deliverables is None


@pytest.mark.asyncio
async def test_counter_with_only_amount(integration_client):
    """Test counter with only amount (no message or deliverables).
    
    Requirements: 1.2
    """
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
        counter_amount=1500.0
    )
    
    # Verify status transition
    assert countered.status == DealStatus.countered
    
    # Verify only amount is set
    assert countered.counter_message is None
    assert countered.counter_amount == 1500.0
    assert countered.counter_deliverables is None
    
    # Verify original offer preserved
    assert countered.offer_amount == 1000.0
    assert countered.deliverables == "Original deliverables"
    
    # Verify counter_history
    assert len(countered.counter_history) == 1
    assert countered.counter_history[0].author == "creator"
    assert countered.counter_history[0].message is None
    assert countered.counter_history[0].proposed_amount == 1500.0
    assert countered.counter_history[0].proposed_deliverables is None


@pytest.mark.asyncio
async def test_counter_with_all_fields(integration_client):
    """Test counter with message, amount, and deliverables.
    
    Requirements: 1.1, 1.2, 1.3
    """
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
    
    # Counter with all fields
    countered = await service.counter_deal(
        deal.id,
        message="I can do this for a higher rate",
        counter_amount=1800.0,
        counter_deliverables="Modified deliverables with extra content"
    )
    
    # Verify status transition
    assert countered.status == DealStatus.countered
    
    # Verify all fields are set
    assert countered.counter_message == "I can do this for a higher rate"
    assert countered.counter_amount == 1800.0
    assert countered.counter_deliverables == "Modified deliverables with extra content"
    
    # Verify original offer preserved
    assert countered.offer_amount == 1000.0
    assert countered.deliverables == "Original deliverables"
    
    # Verify counter_history
    assert len(countered.counter_history) == 1
    assert countered.counter_history[0].author == "creator"
    assert countered.counter_history[0].message == "I can do this for a higher rate"
    assert countered.counter_history[0].proposed_amount == 1800.0
    assert countered.counter_history[0].proposed_deliverables == "Modified deliverables with extra content"


@pytest.mark.asyncio
async def test_counter_amount_at_max_boundary(integration_client):
    """Test counter with amount exactly at MAX_OFFER_AMOUNT boundary.
    
    This tests that the maximum allowed counter amount is accepted.
    Requirements: 1.5, 1.6
    """
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
    
    # Counter with amount at MAX_OFFER_AMOUNT
    max_amount = settings.MAX_OFFER_AMOUNT
    countered = await service.counter_deal(
        deal.id,
        message="Maximum counter offer",
        counter_amount=max_amount
    )
    
    # Verify status transition
    assert countered.status == DealStatus.countered
    
    # Verify counter amount is set to max
    assert countered.counter_amount == max_amount
    assert countered.counter_message == "Maximum counter offer"
    
    # Verify original offer preserved
    assert countered.offer_amount == 1000.0
    
    # Verify counter_history
    assert len(countered.counter_history) == 1
    assert countered.counter_history[0].proposed_amount == max_amount


@pytest.mark.asyncio
async def test_counter_on_nonexistent_deal_returns_404(integration_client):
    """Test counter on non-existent deal raises DealNotFoundError.
    
    This should result in a 404 response when called from the API endpoint.
    Requirements: 1.6
    """
    client, stores = integration_client
    from app.core.database import get_database
    from app.main import app
    db = app.dependency_overrides[get_database]()
    service = DealService(db)
    
    # Try to counter a non-existent deal
    with pytest.raises(DealNotFoundError):
        await service.counter_deal(
            "nonexistent_deal_id_12345",
            message="This should fail"
        )
