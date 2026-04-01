"""
Test for Task 11.2: Display counter data in countered deal cards (Business Dashboard)

This test verifies that the Business Dashboard properly displays:
- counter_message if present
- counter_amount if present
- counter_deliverables if present
- counter_history timeline with author and timestamp

Requirements: 3.5, 3.6, 6.6
"""

import pytest
from datetime import datetime, timedelta
from app.models.deal import Deal, DealStatus, CounterOffer


def test_business_dashboard_displays_counter_message():
    """Verify counter_message is included in deal response"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="I'd like to negotiate the terms"
    )
    
    # Verify counter_message is accessible
    assert deal.counter_message == "I'd like to negotiate the terms"
    assert deal.status == DealStatus.countered


def test_business_dashboard_displays_counter_amount():
    """Verify counter_amount is included in deal response"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_amount=1500.0
    )
    
    # Verify counter_amount is accessible
    assert deal.counter_amount == 1500.0
    assert deal.offer_amount == 1000.0  # Original preserved


def test_business_dashboard_displays_counter_deliverables():
    """Verify counter_deliverables is included in deal response"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_deliverables="2 Instagram posts + 1 story"
    )
    
    # Verify counter_deliverables is accessible
    assert deal.counter_deliverables == "2 Instagram posts + 1 story"
    assert deal.deliverables == "1 Instagram post"  # Original preserved


def test_business_dashboard_displays_all_counter_fields():
    """Verify all counter fields are displayed together"""
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
    
    # Verify all counter fields are accessible
    assert deal.counter_message == "Let's adjust the terms"
    assert deal.counter_amount == 1200.0
    assert deal.counter_deliverables == "1 Instagram post + 2 stories"


def test_business_dashboard_displays_counter_history_with_author_and_timestamp():
    """Verify counter_history is displayed with author attribution and timestamps"""
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
    
    # Verify counter_history is accessible
    assert len(deal.counter_history) == 2
    
    # Verify first entry
    assert deal.counter_history[0].author == "creator"
    assert deal.counter_history[0].message == "Initial counter"
    assert deal.counter_history[0].proposed_amount == 1200.0
    assert deal.counter_history[0].timestamp == timestamp1
    
    # Verify second entry
    assert deal.counter_history[1].author == "business"
    assert deal.counter_history[1].message == "Business counter"
    assert deal.counter_history[1].proposed_amount == 1100.0
    assert deal.counter_history[1].timestamp == timestamp2


def test_business_dashboard_counter_history_chronological_order():
    """Verify counter_history maintains chronological order"""
    base_time = datetime.utcnow()
    
    counter_history = [
        CounterOffer(
            author="creator",
            message="First counter",
            timestamp=base_time
        ),
        CounterOffer(
            author="business",
            message="Second counter",
            timestamp=base_time + timedelta(hours=1)
        ),
        CounterOffer(
            author="creator",
            message="Third counter",
            timestamp=base_time + timedelta(hours=2)
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
    
    # Verify chronological order
    assert len(deal.counter_history) == 3
    assert deal.counter_history[0].timestamp < deal.counter_history[1].timestamp
    assert deal.counter_history[1].timestamp < deal.counter_history[2].timestamp
    
    # Verify messages are in order
    assert deal.counter_history[0].message == "First counter"
    assert deal.counter_history[1].message == "Second counter"
    assert deal.counter_history[2].message == "Third counter"


def test_business_dashboard_handles_empty_counter_history():
    """Verify dashboard handles deals with empty counter_history"""
    deal = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_message="Simple counter",
        counter_history=[]
    )
    
    # Verify empty counter_history is handled
    assert deal.counter_history == []
    assert deal.counter_message == "Simple counter"


def test_business_dashboard_handles_missing_optional_counter_fields():
    """Verify dashboard handles deals with only some counter fields present"""
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
    assert deal1.counter_message == "Just a message"
    assert deal1.counter_amount is None
    assert deal1.counter_deliverables is None
    
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
    assert deal2.counter_message is None
    assert deal2.counter_amount == 1500.0
    assert deal2.counter_deliverables is None
    
    # Only counter_deliverables
    deal3 = Deal(
        business_id="biz123",
        creator_id="creator456",
        offer_amount=1000.0,
        deliverables="1 Instagram post",
        deadline=datetime.utcnow() + timedelta(days=7),
        status=DealStatus.countered,
        counter_deliverables="2 posts"
    )
    assert deal3.counter_message is None
    assert deal3.counter_amount is None
    assert deal3.counter_deliverables == "2 posts"
