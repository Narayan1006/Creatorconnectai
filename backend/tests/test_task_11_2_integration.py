"""
Integration test for Task 11.2: Display counter data in Business Dashboard

This test verifies that the Deal model and DealResponse properly serialize
counter data for display in the Business Dashboard.

Requirements: 3.5, 3.6, 6.6
"""

import pytest
from datetime import datetime, timedelta
from app.models.deal import Deal, DealStatus, CounterOffer, DealResponse


def test_deal_response_includes_counter_message():
    """Test that DealResponse serializes counter_message"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="I'd like to negotiate the terms"
    )
    
    # Convert to response model
    response = DealResponse(**deal.model_dump(by_alias=True))
    
    # Verify counter_message is in response
    assert response.counter_message == "I'd like to negotiate the terms"


def test_deal_response_includes_counter_amount():
    """Test that DealResponse serializes counter_amount"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1500.0
    )
    
    response = DealResponse(**deal.model_dump(by_alias=True))
    assert response.counter_amount == 1500.0


def test_deal_response_includes_counter_deliverables():
    """Test that DealResponse serializes counter_deliverables"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_deliverables="2 Instagram posts + 1 story"
    )
    
    response = DealResponse(**deal.model_dump(by_alias=True))
    assert response.counter_deliverables == "2 Instagram posts + 1 story"


def test_deal_response_includes_all_counter_fields():
    """Test that DealResponse serializes all counter fields together"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Let's adjust the terms",
        counter_amount=1200.0,
        counter_deliverables="1 Instagram post + 2 stories"
    )
    
    response = DealResponse(**deal.model_dump(by_alias=True))
    
    assert response.counter_message == "Let's adjust the terms"
    assert response.counter_amount == 1200.0
    assert response.counter_deliverables == "1 Instagram post + 2 stories"


def test_deal_response_includes_counter_history():
    """Test that DealResponse serializes counter_history with author and timestamp"""
    timestamp1 = datetime.utcnow()
    timestamp2 = timestamp1 + timedelta(hours=1)
    
    counter_history = [
        CounterOffer(
            author="creator",
            message="Initial counter",
            proposed_amount=1200.0,
            timestamp=timestamp1
        ),
        CounterOffer(
            author="business",
            message="Business counter",
            proposed_amount=1100.0,
            timestamp=timestamp2
        )
    ]
    
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_history=counter_history
    )
    
    response = DealResponse(**deal.model_dump(by_alias=True))
    
    # Verify counter_history is in response
    assert len(response.counter_history) == 2
    
    # Verify first entry
    assert response.counter_history[0].author == "creator"
    assert response.counter_history[0].message == "Initial counter"
    assert response.counter_history[0].proposed_amount == 1200.0
    assert response.counter_history[0].timestamp == timestamp1
    
    # Verify second entry
    assert response.counter_history[1].author == "business"
    assert response.counter_history[1].message == "Business counter"
    assert response.counter_history[1].proposed_amount == 1100.0
    assert response.counter_history[1].timestamp == timestamp2


def test_deal_response_json_serialization():
    """Test that DealResponse can be serialized to JSON with all counter fields"""
    timestamp = datetime.utcnow()
    
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Negotiate terms",
        counter_amount=1500.0,
        counter_deliverables="2 posts",
        counter_history=[
            CounterOffer(
                author="creator",
                message="Counter",
                proposed_amount=1500.0,
                timestamp=timestamp
            )
        ]
    )
    
    response = DealResponse(**deal.model_dump(by_alias=True))
    
    # Serialize to JSON
    json_data = response.model_dump(mode='json')
    
    # Verify all counter fields are in JSON
    assert json_data["counter_message"] == "Negotiate terms"
    assert json_data["counter_amount"] == 1500.0
    assert json_data["counter_deliverables"] == "2 posts"
    assert len(json_data["counter_history"]) == 1
    assert json_data["counter_history"][0]["author"] == "creator"


def test_deal_response_handles_partial_counter_fields():
    """Test that DealResponse handles deals with only some counter fields"""
    # Only counter_message
    deal1 = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Just a message"
    )
    
    response1 = DealResponse(**deal1.model_dump(by_alias=True))
    assert response1.counter_message == "Just a message"
    assert response1.counter_amount is None
    assert response1.counter_deliverables is None
    
    # Only counter_amount
    deal2 = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1500.0
    )
    
    response2 = DealResponse(**deal2.model_dump(by_alias=True))
    assert response2.counter_message is None
    assert response2.counter_amount == 1500.0
    assert response2.counter_deliverables is None
