"""
Unit tests for DealResponse model with counter fields.

Verifies that DealResponse includes and serializes counter fields correctly.
"""

from datetime import datetime, timezone

from app.models.deal import DealResponse, DealStatus, PaymentStatus, CounterOffer


class TestDealResponseCounterFields:
    """Test DealResponse includes counter negotiation fields."""

    def test_deal_response_with_all_counter_fields(self):
        """Test DealResponse with all counter fields populated."""
        counter_history = [
            CounterOffer(
                author="creator",
                message="Can we adjust?",
                proposed_amount=500.0,
                proposed_deliverables="2 posts",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        response = DealResponse(
            _id="deal123",
            business_id="biz1",
            creator_id="creator1",
            offer_amount=1000.0,
            deliverables="3 posts",
            deadline=datetime.now(timezone.utc),
            status=DealStatus.countered,
            ad_idea="Great ad concept",
            counter_message="Can we adjust the timeline?",
            counter_amount=500.0,
            counter_deliverables="2 posts instead",
            counter_history=counter_history,
            payment_status=PaymentStatus.not_triggered,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.counter_message == "Can we adjust the timeline?"
        assert response.counter_amount == 500.0
        assert response.counter_deliverables == "2 posts instead"
        assert len(response.counter_history) == 1
        assert response.counter_history[0].author == "creator"

    def test_deal_response_with_no_counter_fields(self):
        """Test DealResponse with counter fields as None (default)."""
        response = DealResponse(
            _id="deal123",
            business_id="biz1",
            creator_id="creator1",
            offer_amount=1000.0,
            deliverables="3 posts",
            deadline=datetime.now(timezone.utc),
            status=DealStatus.pending,
            payment_status=PaymentStatus.not_triggered,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.counter_message is None
        assert response.counter_amount is None
        assert response.counter_deliverables is None
        assert response.counter_history == []

    def test_deal_response_with_partial_counter_fields(self):
        """Test DealResponse with only some counter fields populated."""
        response = DealResponse(
            _id="deal123",
            business_id="biz1",
            creator_id="creator1",
            offer_amount=1000.0,
            deliverables="3 posts",
            deadline=datetime.now(timezone.utc),
            status=DealStatus.countered,
            counter_message="Let's discuss",
            counter_amount=None,
            counter_deliverables=None,
            payment_status=PaymentStatus.not_triggered,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.counter_message == "Let's discuss"
        assert response.counter_amount is None
        assert response.counter_deliverables is None

    def test_deal_response_serialization_with_counter_fields(self):
        """Test that DealResponse serializes counter fields correctly."""
        response = DealResponse(
            _id="deal123",
            business_id="biz1",
            creator_id="creator1",
            offer_amount=1000.0,
            deliverables="3 posts",
            deadline=datetime.now(timezone.utc),
            status=DealStatus.countered,
            counter_message="Counter message",
            counter_amount=750.0,
            counter_deliverables="2 posts",
            payment_status=PaymentStatus.not_triggered,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        data = response.model_dump()
        assert "counter_message" in data
        assert "counter_amount" in data
        assert "counter_deliverables" in data
        assert "counter_history" in data
        assert data["counter_message"] == "Counter message"
        assert data["counter_amount"] == 750.0
        assert data["counter_deliverables"] == "2 posts"

    def test_deal_response_with_ad_idea_and_counter_fields(self):
        """Test DealResponse with both ad_idea and counter fields."""
        response = DealResponse(
            _id="deal123",
            business_id="biz1",
            creator_id="creator1",
            offer_amount=1000.0,
            deliverables="3 posts",
            deadline=datetime.now(timezone.utc),
            status=DealStatus.countered,
            ad_idea="Amazing campaign idea",
            counter_message="Can we adjust?",
            counter_amount=800.0,
            payment_status=PaymentStatus.not_triggered,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.ad_idea == "Amazing campaign idea"
        assert response.counter_message == "Can we adjust?"
        assert response.counter_amount == 800.0
