"""
Property-based tests for Creator profile validation and public serialization.

Property 7 (Req 2.2): engagement_rate validation — values outside [0.0, 1.0] are rejected
Property 13 (Req 10.3): embedding excluded from public response
"""
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from pydantic import ValidationError

from app.models.creator import Creator, CreatorCreate, CreatorPublic

# ---------------------------------------------------------------------------
# Shared valid creator data
# ---------------------------------------------------------------------------

VALID_CREATOR_DATA = {
    "name": "Test Creator",
    "avatar_url": "https://example.com/avatar.jpg",
    "niche": ["tech", "gaming"],
    "platform": "youtube",
    "followers": 10000,
    "engagement_rate": 0.05,
    "bio": "A tech and gaming creator.",
    "portfolio_url": None,
}


# ---------------------------------------------------------------------------
# Property 7: engagement_rate validation
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------

@given(
    rate=st.one_of(
        st.floats(max_value=-0.001, allow_nan=False),
        st.floats(min_value=1.001, allow_nan=False, allow_infinity=False),
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_invalid_engagement_rate_rejected(rate):
    """
    Property 7: For any float outside [0.0, 1.0], CreatorCreate must raise
    a ValidationError (HTTP 422).

    **Validates: Requirements 2.2**
    """
    with pytest.raises(ValidationError):
        CreatorCreate(**{**VALID_CREATOR_DATA, "engagement_rate": rate})


@given(rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_valid_engagement_rate_accepted(rate):
    """
    Property 7 (positive case): For any float in [0.0, 1.0], CreatorCreate
    must succeed without raising a ValidationError.

    **Validates: Requirements 2.2**
    """
    creator = CreatorCreate(**{**VALID_CREATOR_DATA, "engagement_rate": rate})
    assert creator.engagement_rate == rate


# ---------------------------------------------------------------------------
# Property 13: embedding excluded from public response
# Validates: Requirements 10.3
# ---------------------------------------------------------------------------

@given(
    embedding=st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=1,
        max_size=10,
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_embedding_excluded_from_public_response(embedding):
    """
    Property 13: For any Creator with an embedding, serializing to CreatorPublic
    must never include the embedding field.

    **Validates: Requirements 10.3**
    """
    creator = Creator(**{**VALID_CREATOR_DATA, "embedding": embedding})
    pub = CreatorPublic(**creator.model_dump(by_alias=True))
    assert "embedding" not in pub.model_dump()


@given(
    embedding=st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=1,
        max_size=10,
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
def test_embedding_excluded_from_public_response_model_dump_keys(embedding):
    """
    Property 13 (key check): CreatorPublic.model_dump() keys must never contain
    'embedding' regardless of the embedding value passed to Creator.

    **Validates: Requirements 10.3**
    """
    creator = Creator(**{**VALID_CREATOR_DATA, "embedding": embedding})
    pub = CreatorPublic(**creator.model_dump(by_alias=True))
    assert "embedding" not in pub.model_dump().keys()
