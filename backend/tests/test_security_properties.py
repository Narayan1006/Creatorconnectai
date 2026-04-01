"""
Property-based tests for API Security and Input Validation.

Property 14 (Req 13.2): For any deal creation request, a non-positive or
    out-of-range offer_amount must be rejected with HTTP 422 by server-side
    validation.

Property 15 (Req 13.3, 13.5): For any content submission request, a
    content_url whose domain is NOT on the trusted CDN allowlist must be
    rejected with HTTP 422.

Uses hypothesis; no real database required — validation is tested at the
Pydantic model layer (Property 14) and via FastAPI TestClient with mocked
dependencies (Property 15).
"""

import sys
import types
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Stub motor so the module loads without a real MongoDB
# ---------------------------------------------------------------------------

def _stub_motor():
    if "motor" not in sys.modules:
        motor_mod = types.ModuleType("motor")
        motor_async_mod = types.ModuleType("motor.motor_asyncio")
        motor_async_mod.AsyncIOMotorClient = MagicMock
        motor_async_mod.AsyncIOMotorDatabase = MagicMock
        motor_mod.motor_asyncio = motor_async_mod
        sys.modules["motor"] = motor_mod
        sys.modules["motor.motor_asyncio"] = motor_async_mod


_stub_motor()

from app.models.deal import DealCreate
from app.routers.deals import _validate_content_url_domain, _get_allowed_domains
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-positive offer amounts (zero, negative, very negative)
non_positive_amounts = st.one_of(
    st.just(0.0),
    st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False),
)

# Over-limit offer amounts (above 1,000,000)
over_limit_amounts = st.floats(
    min_value=1_000_001.0,
    max_value=1e15,
    allow_nan=False,
    allow_infinity=False,
)

# Valid offer amounts
valid_amounts = st.floats(
    min_value=0.01,
    max_value=1_000_000.0,
    allow_nan=False,
    allow_infinity=False,
)

# Trusted CDN domains from the allowlist
TRUSTED_DOMAINS = [
    "cdn.example.com",
    "storage.googleapis.com",
    "s3.amazonaws.com",
    "cloudfront.net",
    "cdn.cloudflare.com",
    "media.instagram.com",
    "i.ytimg.com",
    "pbs.twimg.com",
]

# Non-allowlisted domains: generate hostnames that are NOT in the trusted list
# and don't end with any trusted domain
_untrusted_tlds = ["com", "net", "org", "io", "co", "xyz"]
_untrusted_names = ["evil", "attacker", "malicious", "untrusted", "random", "hack", "bad"]

untrusted_domains = st.builds(
    lambda name, tld: f"{name}.{tld}",
    name=st.sampled_from(_untrusted_names),
    tld=st.sampled_from(_untrusted_tlds),
).filter(
    lambda d: not any(
        d == trusted or d.endswith("." + trusted)
        for trusted in TRUSTED_DOMAINS
    )
)

# URLs with untrusted domains
untrusted_urls = st.builds(
    lambda domain, path: f"https://{domain}/{path}",
    domain=untrusted_domains,
    path=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_/"),
    ),
)

# URLs with trusted domains
trusted_urls = st.builds(
    lambda domain, path: f"https://{domain}/{path}",
    domain=st.sampled_from(TRUSTED_DOMAINS),
    path=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_/"),
    ),
)

# Valid deal creation payload (excluding offer_amount)
_valid_deadline = datetime(2026, 1, 1, tzinfo=timezone.utc)

valid_deal_base = st.fixed_dictionaries({
    "business_id": st.uuids().map(str),
    "creator_id": st.uuids().map(str),
    "deliverables": st.text(
        min_size=1,
        max_size=100,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    ),
    "deadline": st.just(_valid_deadline),
})


# ---------------------------------------------------------------------------
# Property 14: Offer amount validation
# Non-positive offer_amount rejected with HTTP 422 (Pydantic ValidationError)
# Validates: Requirements 13.2
# ---------------------------------------------------------------------------

@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(base=valid_deal_base, amount=non_positive_amounts)
def test_non_positive_offer_amount_rejected(base, amount):
    """
    Property 14: For any deal creation request with a non-positive offer_amount,
    the Pydantic model must raise a ValidationError (which FastAPI converts to HTTP 422).

    **Validates: Requirements 13.2**
    """
    payload = {**base, "offer_amount": amount}
    with pytest.raises(ValidationError) as exc_info:
        DealCreate(**payload)

    errors = exc_info.value.errors()
    assert any("offer_amount" in str(e.get("loc", "")) for e in errors), (
        f"Expected validation error on offer_amount, got: {errors}"
    )


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(base=valid_deal_base, amount=over_limit_amounts)
def test_over_limit_offer_amount_rejected(base, amount):
    """
    Property 14 (over-limit): For any deal creation request with an offer_amount
    exceeding the configured maximum, the Pydantic model must raise a ValidationError.

    **Validates: Requirements 13.2**
    """
    payload = {**base, "offer_amount": amount}
    with pytest.raises(ValidationError) as exc_info:
        DealCreate(**payload)

    errors = exc_info.value.errors()
    assert any("offer_amount" in str(e.get("loc", "")) for e in errors), (
        f"Expected validation error on offer_amount, got: {errors}"
    )


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(base=valid_deal_base, amount=valid_amounts)
def test_valid_offer_amount_accepted(base, amount):
    """
    Property 14 (positive case): For any deal creation request with a valid
    positive offer_amount within limits, the Pydantic model must accept it.

    **Validates: Requirements 13.2**
    """
    payload = {**base, "offer_amount": amount}
    deal = DealCreate(**payload)
    assert deal.offer_amount == amount


# ---------------------------------------------------------------------------
# Property 15: Content URL domain allowlist
# Non-allowlisted content URLs rejected with HTTP 422
# Validates: Requirements 13.3, 13.5
# ---------------------------------------------------------------------------

@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(url=untrusted_urls)
def test_non_allowlisted_content_url_rejected(url):
    """
    Property 15: For any content submission request with a content_url whose
    domain is NOT on the trusted CDN allowlist, the validation must raise
    HTTP 422 with a descriptive error.

    **Validates: Requirements 13.3, 13.5**
    """
    with pytest.raises(HTTPException) as exc_info:
        _validate_content_url_domain(url)

    assert exc_info.value.status_code == 422, (
        f"Expected HTTP 422 for untrusted URL '{url}', got {exc_info.value.status_code}"
    )
    assert "not in the trusted CDN allowlist" in exc_info.value.detail, (
        f"Expected descriptive error message, got: {exc_info.value.detail}"
    )


@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(url=trusted_urls)
def test_allowlisted_content_url_accepted(url):
    """
    Property 15 (positive case): For any content submission request with a
    content_url whose domain IS on the trusted CDN allowlist, the validation
    must pass without raising an exception.

    **Validates: Requirements 13.3**
    """
    # Should not raise
    _validate_content_url_domain(url)


# ---------------------------------------------------------------------------
# Unit tests for specific edge cases
# ---------------------------------------------------------------------------

def test_zero_offer_amount_rejected():
    """Req 13.2: offer_amount of exactly 0 must be rejected."""
    with pytest.raises(ValidationError):
        DealCreate(
            business_id="biz_1",
            creator_id="creator_1",
            offer_amount=0.0,
            deliverables="1 post",
            deadline=_valid_deadline,
        )


def test_negative_offer_amount_rejected():
    """Req 13.2: Negative offer_amount must be rejected."""
    with pytest.raises(ValidationError):
        DealCreate(
            business_id="biz_1",
            creator_id="creator_1",
            offer_amount=-100.0,
            deliverables="1 post",
            deadline=_valid_deadline,
        )


def test_max_offer_amount_accepted():
    """Req 13.2: offer_amount at exactly the max limit must be accepted."""
    deal = DealCreate(
        business_id="biz_1",
        creator_id="creator_1",
        offer_amount=1_000_000.0,
        deliverables="1 post",
        deadline=_valid_deadline,
    )
    assert deal.offer_amount == 1_000_000.0


def test_over_max_offer_amount_rejected():
    """Req 13.2: offer_amount above the max limit must be rejected."""
    with pytest.raises(ValidationError):
        DealCreate(
            business_id="biz_1",
            creator_id="creator_1",
            offer_amount=1_000_001.0,
            deliverables="1 post",
            deadline=_valid_deadline,
        )


def test_trusted_cdn_domain_accepted():
    """Req 13.3: A URL from a trusted CDN domain must pass validation."""
    _validate_content_url_domain("https://cdn.example.com/video/reel_123.mp4")


def test_untrusted_domain_rejected_with_422():
    """Req 13.3, 13.5: A URL from an untrusted domain must return HTTP 422."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_content_url_domain("https://evil.com/malicious.mp4")

    assert exc_info.value.status_code == 422
    assert "evil.com" in exc_info.value.detail


def test_subdomain_of_trusted_domain_accepted():
    """Req 13.3: A subdomain of a trusted CDN domain must pass validation."""
    _validate_content_url_domain("https://bucket.s3.amazonaws.com/content/video.mp4")


def test_domain_that_ends_with_trusted_but_is_not_subdomain_rejected():
    """Req 13.3: A domain like 'evils3.amazonaws.com' must NOT be accepted."""
    # 'evils3.amazonaws.com' ends with 's3.amazonaws.com' but is not a subdomain
    # Our check uses endswith("." + domain), so 'evils3.amazonaws.com' won't match
    # because it doesn't end with '.s3.amazonaws.com'
    with pytest.raises(HTTPException) as exc_info:
        _validate_content_url_domain("https://evils3.amazonaws.com/content.mp4")
    assert exc_info.value.status_code == 422


def test_error_message_contains_domain():
    """Req 13.5: The 422 error message must contain the offending domain."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_content_url_domain("https://attacker.io/payload.mp4")

    assert "attacker.io" in exc_info.value.detail


def test_allowed_domains_list_contains_expected_domains():
    """Req 13.3: The allowlist must contain all expected trusted CDN domains."""
    allowed = _get_allowed_domains()
    for domain in TRUSTED_DOMAINS:
        assert domain in allowed, f"Expected '{domain}' in allowlist, got: {allowed}"
