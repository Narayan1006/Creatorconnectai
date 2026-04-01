"""
Unit tests for CounterOffer model and Deal model counter field extensions.

Tests cover:
- CounterOffer model validation (author, proposed_amount)
- Deal model counter field defaults
- Deal model counter_amount validation
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.models.deal import CounterOffer, Deal, DealStatus, PaymentStatus


class TestCounterOfferModel:
    """Tests for CounterOffer embedded model."""

    def test_counter_offer_with_all_fields(self):
        """CounterOffer accepts all fields when valid."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(
            author="creator",
            message="Can we increase the budget?",
            proposed_amount=750.0,
            proposed_deliverables="2 Instagram Reels",
            timestamp=now
        )
        
        assert counter.author == "creator"
        assert counter.message == "Can we increase the budget?"
        assert counter.proposed_amount == 750.0
        assert counter.proposed_deliverables == "2 Instagram Reels"
        assert counter.timestamp == now

    def test_counter_offer_with_minimal_fields(self):
        """CounterOffer accepts only required fields."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(
            author="business",
            timestamp=now
        )
        
        assert counter.author == "business"
        assert counter.message is None
        assert counter.proposed_amount is None
        assert counter.proposed_deliverables is None
        assert counter.timestamp == now

    def test_counter_offer_author_validation_creator(self):
        """CounterOffer accepts 'creator' as valid author."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(author="creator", timestamp=now)
        assert counter.author == "creator"

    def test_counter_offer_author_validation_business(self):
        """CounterOffer accepts 'business' as valid author."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(author="business", timestamp=now)
        assert counter.author == "business"

    def test_counter_offer_author_validation_invalid(self):
        """CounterOffer rejects invalid author values."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            CounterOffer(author="admin", timestamp=now)
        
        assert "author must be 'creator' or 'business'" in str(exc_info.value)

    def test_counter_offer_proposed_amount_positive(self):
        """CounterOffer accepts positive proposed_amount."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(
            author="creator",
            proposed_amount=100.0,
            timestamp=now
        )
        assert counter.proposed_amount == 100.0

    def test_counter_offer_proposed_amount_zero(self):
        """CounterOffer rejects zero proposed_amount."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            CounterOffer(
                author="creator",
                proposed_amount=0.0,
                timestamp=now
            )
        
        assert "proposed_amount must be positive" in str(exc_info.value)

    def test_counter_offer_proposed_amount_negative(self):
        """CounterOffer rejects negative proposed_amount."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            CounterOffer(
                author="creator",
                proposed_amount=-50.0,
                timestamp=now
            )
        
        assert "proposed_amount must be positive" in str(exc_info.value)

    def test_counter_offer_proposed_amount_none(self):
        """CounterOffer accepts None for proposed_amount."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(
            author="creator",
            proposed_amount=None,
            timestamp=now
        )
        assert counter.proposed_amount is None


class TestDealModelCounterFields:
    """Tests for Deal model counter field extensions."""

    def test_deal_counter_fields_default_to_none(self):
        """New Deal has counter fields defaulting to None."""
        now = datetime.now(timezone.utc)
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            created_at=now,
            updated_at=now
        )
        
        assert deal.counter_message is None
        assert deal.counter_amount is None
        assert deal.counter_deliverables is None
        assert deal.counter_history == []

    def test_deal_with_counter_message(self):
        """Deal accepts counter_message."""
        now = datetime.now(timezone.utc)
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_message="Can we negotiate?",
            created_at=now,
            updated_at=now
        )
        
        assert deal.counter_message == "Can we negotiate?"

    def test_deal_with_counter_amount(self):
        """Deal accepts positive counter_amount."""
        now = datetime.now(timezone.utc)
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_amount=750.0,
            created_at=now,
            updated_at=now
        )
        
        assert deal.counter_amount == 750.0

    def test_deal_counter_amount_validation_zero(self):
        """Deal rejects zero counter_amount."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            Deal(
                business_id="biz_001",
                creator_id="creator_001",
                offer_amount=500.0,
                deliverables="1 Instagram Reel",
                deadline=now,
                counter_amount=0.0,
                created_at=now,
                updated_at=now
            )
        
        assert "counter_amount must be positive" in str(exc_info.value)

    def test_deal_counter_amount_validation_negative(self):
        """Deal rejects negative counter_amount."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            Deal(
                business_id="biz_001",
                creator_id="creator_001",
                offer_amount=500.0,
                deliverables="1 Instagram Reel",
                deadline=now,
                counter_amount=-100.0,
                created_at=now,
                updated_at=now
            )
        
        assert "counter_amount must be positive" in str(exc_info.value)

    def test_deal_with_counter_deliverables(self):
        """Deal accepts counter_deliverables."""
        now = datetime.now(timezone.utc)
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_deliverables="2 Instagram Reels",
            created_at=now,
            updated_at=now
        )
        
        assert deal.counter_deliverables == "2 Instagram Reels"

    def test_deal_with_counter_history(self):
        """Deal accepts counter_history list."""
        now = datetime.now(timezone.utc)
        counter1 = CounterOffer(
            author="creator",
            message="First counter",
            proposed_amount=600.0,
            timestamp=now
        )
        counter2 = CounterOffer(
            author="business",
            message="Business response",
            proposed_amount=550.0,
            timestamp=now
        )
        
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_history=[counter1, counter2],
            created_at=now,
            updated_at=now
        )
        
        assert len(deal.counter_history) == 2
        assert deal.counter_history[0].author == "creator"
        assert deal.counter_history[1].author == "business"

    def test_deal_with_all_counter_fields(self):
        """Deal accepts all counter fields together."""
        now = datetime.now(timezone.utc)
        counter = CounterOffer(
            author="creator",
            message="Counter message",
            proposed_amount=700.0,
            timestamp=now
        )
        
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_message="Latest counter",
            counter_amount=750.0,
            counter_deliverables="2 Reels",
            counter_history=[counter],
            created_at=now,
            updated_at=now
        )
        
        assert deal.counter_message == "Latest counter"
        assert deal.counter_amount == 750.0
        assert deal.counter_deliverables == "2 Reels"
        assert len(deal.counter_history) == 1

    def test_deal_preserves_original_offer_with_counter(self):
        """Deal preserves original offer_amount and deliverables when counter fields are set."""
        now = datetime.now(timezone.utc)
        deal = Deal(
            business_id="biz_001",
            creator_id="creator_001",
            offer_amount=500.0,
            deliverables="1 Instagram Reel",
            deadline=now,
            counter_amount=750.0,
            counter_deliverables="2 Instagram Reels",
            created_at=now,
            updated_at=now
        )
        
        # Original offer fields should remain unchanged
        assert deal.offer_amount == 500.0
        assert deal.deliverables == "1 Instagram Reel"
        # Counter fields should be set
        assert deal.counter_amount == 750.0
        assert deal.counter_deliverables == "2 Instagram Reels"
