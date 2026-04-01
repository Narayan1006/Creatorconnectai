"""
Unit tests for CounterRequest and BusinessCounterRequest models.

Tests validation logic for counter_amount and message fields.
"""

import pytest
from pydantic import ValidationError

from app.routers.deals import CounterRequest, BusinessCounterRequest
from app.core.config import settings


class TestCounterRequest:
    """Test CounterRequest model validation."""

    def test_all_fields_valid(self):
        """Test counter request with all valid fields."""
        req = CounterRequest(
            message="Can we adjust the timeline?",
            counter_amount=500.0,
            counter_deliverables="2 posts instead of 3"
        )
        assert req.message == "Can we adjust the timeline?"
        assert req.counter_amount == 500.0
        assert req.counter_deliverables == "2 posts instead of 3"

    def test_all_fields_none(self):
        """Test counter request with all fields as None."""
        req = CounterRequest()
        assert req.message is None
        assert req.counter_amount is None
        assert req.counter_deliverables is None

    def test_only_message(self):
        """Test counter request with only message."""
        req = CounterRequest(message="Let's discuss")
        assert req.message == "Let's discuss"
        assert req.counter_amount is None
        assert req.counter_deliverables is None

    def test_only_amount(self):
        """Test counter request with only amount."""
        req = CounterRequest(counter_amount=750.0)
        assert req.message is None
        assert req.counter_amount == 750.0
        assert req.counter_deliverables is None

    def test_only_deliverables(self):
        """Test counter request with only deliverables."""
        req = CounterRequest(counter_deliverables="3 Instagram stories")
        assert req.message is None
        assert req.counter_amount is None
        assert req.counter_deliverables == "3 Instagram stories"

    def test_positive_amount_validation(self):
        """Test that positive amounts are accepted."""
        req = CounterRequest(counter_amount=0.01)
        assert req.counter_amount == 0.01

        req = CounterRequest(counter_amount=1000.0)
        assert req.counter_amount == 1000.0

    def test_zero_amount_rejected(self):
        """Test that zero counter_amount is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CounterRequest(counter_amount=0)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "positive" in errors[0]["msg"].lower()

    def test_negative_amount_rejected(self):
        """Test that negative counter_amount is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CounterRequest(counter_amount=-100.0)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "positive" in errors[0]["msg"].lower()

    def test_amount_exceeding_max_rejected(self):
        """Test that counter_amount exceeding MAX_OFFER_AMOUNT is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CounterRequest(counter_amount=settings.MAX_OFFER_AMOUNT + 1)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "maximum" in errors[0]["msg"].lower()

    def test_amount_at_max_accepted(self):
        """Test that counter_amount exactly at MAX_OFFER_AMOUNT is accepted."""
        req = CounterRequest(counter_amount=settings.MAX_OFFER_AMOUNT)
        assert req.counter_amount == settings.MAX_OFFER_AMOUNT

    def test_empty_message_rejected(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CounterRequest(message="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "empty" in errors[0]["msg"].lower()

    def test_whitespace_only_message_rejected(self):
        """Test that whitespace-only message is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CounterRequest(message="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "empty" in errors[0]["msg"].lower()

    def test_valid_message_with_whitespace(self):
        """Test that message with leading/trailing whitespace is accepted."""
        req = CounterRequest(message="  Valid message  ")
        assert req.message == "  Valid message  "


class TestBusinessCounterRequest:
    """Test BusinessCounterRequest model validation."""

    def test_all_fields_valid(self):
        """Test business counter request with all valid fields."""
        req = BusinessCounterRequest(
            message="We can meet you halfway",
            counter_amount=600.0,
            counter_deliverables="2 posts with stories"
        )
        assert req.message == "We can meet you halfway"
        assert req.counter_amount == 600.0
        assert req.counter_deliverables == "2 posts with stories"

    def test_all_fields_none(self):
        """Test business counter request with all fields as None."""
        req = BusinessCounterRequest()
        assert req.message is None
        assert req.counter_amount is None
        assert req.counter_deliverables is None

    def test_zero_amount_rejected(self):
        """Test that zero counter_amount is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessCounterRequest(counter_amount=0)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "positive" in errors[0]["msg"].lower()

    def test_negative_amount_rejected(self):
        """Test that negative counter_amount is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessCounterRequest(counter_amount=-50.0)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "positive" in errors[0]["msg"].lower()

    def test_amount_exceeding_max_rejected(self):
        """Test that counter_amount exceeding MAX_OFFER_AMOUNT is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessCounterRequest(counter_amount=settings.MAX_OFFER_AMOUNT + 100)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("counter_amount",)
        assert "maximum" in errors[0]["msg"].lower()

    def test_amount_at_max_accepted(self):
        """Test that counter_amount exactly at MAX_OFFER_AMOUNT is accepted."""
        req = BusinessCounterRequest(counter_amount=settings.MAX_OFFER_AMOUNT)
        assert req.counter_amount == settings.MAX_OFFER_AMOUNT

    def test_empty_message_rejected(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessCounterRequest(message="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "empty" in errors[0]["msg"].lower()

    def test_whitespace_only_message_rejected(self):
        """Test that whitespace-only message is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessCounterRequest(message="   \t\n   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message",)
        assert "empty" in errors[0]["msg"].lower()

    def test_positive_amount_validation(self):
        """Test that positive amounts are accepted."""
        req = BusinessCounterRequest(counter_amount=0.01)
        assert req.counter_amount == 0.01

        req = BusinessCounterRequest(counter_amount=999999.99)
        assert req.counter_amount == 999999.99
