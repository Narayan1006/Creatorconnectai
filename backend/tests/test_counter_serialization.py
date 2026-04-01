"""
Integration test for counter field serialization in DealResponse.

Verifies that counter fields are properly included in API responses.
"""

from datetime import datetime, timezone, timedelta
from app.models.deal import Deal, DealResponse, CounterOffer, DealStatus, PaymentStatus


def test_deal_response_includes_counter_fields():
    """DealResponse serializes counter fields correctly."""
    now = datetime.now(timezone.utc)
    
    counter = CounterOffer(
        author="creator",
        message="Can we increase the budget?",
        proposed_amount=750.0,
        proposed_deliverables="2 Instagram Reels",
        timestamp=now
    )
    
    deal = Deal(
        _id="507f1f77bcf86cd799439011",
        business_id="biz_001",
        creator_id="creator_001",
        offer_amount=500.0,
        deliverables="1 Instagram Reel",
        deadline=now + timedelta(days=30),
        status=DealStatus.countered,
        counter_message="Latest counter message",
        counter_amount=800.0,
        counter_deliverables="3 Instagram Reels",
        counter_history=[counter],
        created_at=now,
        updated_at=now
    )
    
    # Convert to DealResponse
    response_data = deal.model_dump(by_alias=True)
    response = DealResponse(**response_data)
    
    # Verify counter fields are present
    assert response.counter_message == "Latest counter message"
    assert response.counter_amount == 800.0
    assert response.counter_deliverables == "3 Instagram Reels"
    assert len(response.counter_history) == 1
    assert response.counter_history[0].author == "creator"
    assert response.counter_history[0].message == "Can we increase the budget?"


def test_deal_response_with_no_counter_fields():
    """DealResponse handles deals without counter fields."""
    now = datetime.now(timezone.utc)
    
    deal = Deal(
        _id="507f1f77bcf86cd799439011",
        business_id="biz_001",
        creator_id="creator_001",
        offer_amount=500.0,
        deliverables="1 Instagram Reel",
        deadline=now + timedelta(days=30),
        status=DealStatus.pending,
        created_at=now,
        updated_at=now
    )
    
    # Convert to DealResponse
    response_data = deal.model_dump(by_alias=True)
    response = DealResponse(**response_data)
    
    # Verify counter fields are None/empty
    assert response.counter_message is None
    assert response.counter_amount is None
    assert response.counter_deliverables is None
    assert response.counter_history == []


def test_deal_response_json_serialization():
    """DealResponse can be serialized to JSON with counter fields."""
    now = datetime.now(timezone.utc)
    
    counter = CounterOffer(
        author="business",
        message="How about this?",
        proposed_amount=650.0,
        timestamp=now
    )
    
    deal = Deal(
        _id="507f1f77bcf86cd799439011",
        business_id="biz_001",
        creator_id="creator_001",
        offer_amount=500.0,
        deliverables="1 Instagram Reel",
        deadline=now + timedelta(days=30),
        status=DealStatus.countered,
        counter_message="Counter message",
        counter_amount=700.0,
        counter_history=[counter],
        created_at=now,
        updated_at=now
    )
    
    # Convert to DealResponse and serialize to JSON
    response_data = deal.model_dump(by_alias=True)
    response = DealResponse(**response_data)
    json_data = response.model_dump(mode='json')
    
    # Verify JSON contains counter fields
    assert json_data["counter_message"] == "Counter message"
    assert json_data["counter_amount"] == 700.0
    assert json_data["counter_deliverables"] is None
    assert len(json_data["counter_history"]) == 1
    assert json_data["counter_history"][0]["author"] == "business"
