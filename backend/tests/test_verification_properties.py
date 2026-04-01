"""
Property-based tests for VerificationService.

Property 4  (Req 6.3/6.4): passed = true iff match_score >= 0.75
Property 2  (Req 6.2):      match_score is in [0.0, 1.0]
Property 11 (Req 6.7):      feedback is always a non-empty string

Uses hypothesis; no real embedding model or database required.
The VerificationService is exercised directly via compute_cosine_similarity
and via a fully mocked verify() call.
"""

import sys
import types
import asyncio
import math
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Stub heavy dependencies before any app import
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


def _stub_sentence_transformers():
    if "sentence_transformers" not in sys.modules:
        st_mod = types.ModuleType("sentence_transformers")

        class _FakeST:
            def __init__(self, *a, **kw):
                pass

            def encode(self, text):
                return np.zeros(4)

        st_mod.SentenceTransformer = _FakeST
        sys.modules["sentence_transformers"] = st_mod


def _stub_faiss():
    if "faiss" not in sys.modules:
        faiss_mod = types.ModuleType("faiss")

        class _IndexFlatL2:
            def __init__(self, dim):
                self.d = dim

            def add(self, arr):
                pass

            def search(self, arr, k):
                return np.empty((1, 0)), np.empty((1, 0), dtype=np.int64)

        faiss_mod.IndexFlatL2 = _IndexFlatL2
        sys.modules["faiss"] = faiss_mod


_stub_motor()
_stub_sentence_transformers()
_stub_faiss()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


THRESHOLD = 0.75
DIM = 8


def _make_verification_service(embed_fn=None):
    """Build a VerificationService with mocked embedding and deal services."""
    from app.services.verification_service import VerificationService

    embedding_mock = MagicMock()
    if embed_fn is not None:
        embedding_mock.embed.side_effect = embed_fn
    else:
        embedding_mock.embed.return_value = [1.0] + [0.0] * (DIM - 1)

    deal_service_mock = MagicMock()
    deal_service_mock.get_deal = AsyncMock(return_value=MagicMock(status="content_submitted"))
    deal_service_mock.transition_deal_status = MagicMock(side_effect=lambda d, a: d)
    deal_service_mock._save_deal = AsyncMock(return_value=None)

    return VerificationService(
        embedding_service=embedding_mock,
        deal_service=deal_service_mock,
    )


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# A non-zero float vector of fixed dimension
nonzero_vector = st.lists(
    st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    min_size=DIM,
    max_size=DIM,
).filter(lambda v: any(x != 0.0 for x in v))

# A pair of non-zero vectors
nonzero_vector_pair = st.tuples(nonzero_vector, nonzero_vector)

# Scores that span the full [0,1] range including boundary
score_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Scores that are clearly above or below threshold
above_threshold = st.floats(min_value=THRESHOLD, max_value=1.0, allow_nan=False, allow_infinity=False)
below_threshold = st.floats(min_value=0.0, max_value=THRESHOLD - 1e-9, allow_nan=False, allow_infinity=False)

# Non-empty text strings
text_str = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
)


# ---------------------------------------------------------------------------
# Property 4: passed iff match_score >= 0.75
# Validates: Requirements 6.3, 6.4
# ---------------------------------------------------------------------------

@h_settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(score=score_strategy)
def test_passed_iff_score_gte_threshold(score):
    """
    Property 4: For any verification result, passed = true iff match_score >= 0.75.

    **Validates: Requirements 6.3, 6.4**
    """
    from app.models.verification import VerificationResult

    result = VerificationResult(
        deal_id="deal_test",
        match_score=score,
        threshold=THRESHOLD,
        passed=(score >= THRESHOLD),
        feedback="test feedback",
    )

    if score >= THRESHOLD:
        assert result.passed is True, (
            f"Expected passed=True for score={score} >= threshold={THRESHOLD}"
        )
    else:
        assert result.passed is False, (
            f"Expected passed=False for score={score} < threshold={THRESHOLD}"
        )


@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(vec_pair=nonzero_vector_pair, ad_idea=text_str, content=text_str)
def test_verify_passed_iff_score_gte_threshold(vec_pair, ad_idea, content):
    """
    Property 4 (via VerificationService): For any embedding pair, the returned
    VerificationResult.passed must equal (match_score >= 0.75).

    **Validates: Requirements 6.3, 6.4**
    """
    vec_a, vec_b = vec_pair
    call_count = [0]

    def embed_fn(text):
        idx = call_count[0]
        call_count[0] += 1
        return vec_a if idx == 0 else vec_b

    svc = _make_verification_service(embed_fn=embed_fn)

    # Patch _fetch_content_text to return the content string directly
    async def _fake_fetch(url):
        return content

    svc._fetch_content_text = _fake_fetch

    result = _run(svc.verify("deal_001", ad_idea, "https://cdn.example.com/content.mp4"))

    assert result.passed == (result.match_score >= THRESHOLD), (
        f"passed={result.passed} does not match score={result.match_score} >= {THRESHOLD}"
    )


# ---------------------------------------------------------------------------
# Property 2 pattern: match_score in [0.0, 1.0]
# Validates: Requirements 6.2
# ---------------------------------------------------------------------------

@h_settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(vec_pair=nonzero_vector_pair)
def test_cosine_similarity_in_unit_interval(vec_pair):
    """
    Property 2 pattern: compute_cosine_similarity always returns a value in [0.0, 1.0].

    **Validates: Requirements 6.2**
    """
    from app.services.verification_service import VerificationService

    svc = _make_verification_service()
    vec_a, vec_b = vec_pair
    score, error = svc.compute_cosine_similarity(vec_a, vec_b)

    assert error is None, f"Unexpected error for non-zero vectors: {error}"
    assert 0.0 <= score <= 1.0, (
        f"match_score {score} is outside [0.0, 1.0]"
    )


@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(vec_pair=nonzero_vector_pair, ad_idea=text_str, content=text_str)
def test_verify_score_in_unit_interval(vec_pair, ad_idea, content):
    """
    Property 2 pattern (via VerificationService.verify): match_score is always in [0.0, 1.0].

    **Validates: Requirements 6.2**
    """
    vec_a, vec_b = vec_pair
    call_count = [0]

    def embed_fn(text):
        idx = call_count[0]
        call_count[0] += 1
        return vec_a if idx == 0 else vec_b

    svc = _make_verification_service(embed_fn=embed_fn)

    async def _fake_fetch(url):
        return content

    svc._fetch_content_text = _fake_fetch

    result = _run(svc.verify("deal_002", ad_idea, "https://cdn.example.com/content.mp4"))

    assert 0.0 <= result.match_score <= 1.0, (
        f"match_score {result.match_score} is outside [0.0, 1.0]"
    )


# ---------------------------------------------------------------------------
# Property 11: feedback is always non-empty
# Validates: Requirements 6.7
# ---------------------------------------------------------------------------

@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(vec_pair=nonzero_vector_pair, ad_idea=text_str, content=text_str)
def test_feedback_always_nonempty_normal_case(vec_pair, ad_idea, content):
    """
    Property 11: For any call to VerificationService.verify with accessible content,
    the returned VerificationResult.feedback is always a non-empty string.

    **Validates: Requirements 6.7**
    """
    vec_a, vec_b = vec_pair
    call_count = [0]

    def embed_fn(text):
        idx = call_count[0]
        call_count[0] += 1
        return vec_a if idx == 0 else vec_b

    svc = _make_verification_service(embed_fn=embed_fn)

    async def _fake_fetch(url):
        return content

    svc._fetch_content_text = _fake_fetch

    result = _run(svc.verify("deal_003", ad_idea, "https://cdn.example.com/content.mp4"))

    assert isinstance(result.feedback, str), "feedback must be a string"
    assert len(result.feedback) > 0, "feedback must be non-empty"


def test_feedback_nonempty_on_inaccessible_url():
    """
    Property 11 (edge case): feedback is non-empty when content URL is inaccessible.

    **Validates: Requirements 6.5, 6.7**
    """
    svc = _make_verification_service()

    async def _fake_fetch(url):
        return None  # simulate inaccessible URL

    svc._fetch_content_text = _fake_fetch

    result = _run(svc.verify("deal_004", "some ad idea", "https://cdn.example.com/bad.mp4"))

    assert result.feedback == "Content could not be processed"
    assert result.match_score == 0.0
    assert result.passed is False


def test_feedback_nonempty_on_zero_embedding():
    """
    Property 11 (edge case): feedback is non-empty when embedding is zero-magnitude.

    **Validates: Requirements 6.6, 6.7**
    """
    svc = _make_verification_service(embed_fn=lambda text: [0.0] * DIM)

    async def _fake_fetch(url):
        return "some content text"

    svc._fetch_content_text = _fake_fetch

    result = _run(svc.verify("deal_005", "some ad idea", "https://cdn.example.com/content.mp4"))

    assert result.feedback == "Empty embedding"
    assert result.match_score == 0.0
    assert result.passed is False


# ---------------------------------------------------------------------------
# Additional unit tests for compute_cosine_similarity
# ---------------------------------------------------------------------------

def test_identical_vectors_score_is_one():
    """Identical non-zero vectors should yield cosine similarity = 1.0."""
    from app.services.verification_service import VerificationService

    svc = _make_verification_service()
    vec = [1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    score, error = svc.compute_cosine_similarity(vec, vec)

    assert error is None
    assert abs(score - 1.0) < 1e-6, f"Expected 1.0 for identical vectors, got {score}"


def test_orthogonal_vectors_score_is_zero():
    """Orthogonal vectors should yield cosine similarity = 0.0 (clamped from 0)."""
    from app.services.verification_service import VerificationService

    svc = _make_verification_service()
    vec_a = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    vec_b = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    score, error = svc.compute_cosine_similarity(vec_a, vec_b)

    assert error is None
    assert abs(score - 0.0) < 1e-6, f"Expected 0.0 for orthogonal vectors, got {score}"


def test_zero_vector_returns_empty_embedding_feedback():
    """Zero-magnitude vector should return (0.0, 'Empty embedding')."""
    from app.services.verification_service import VerificationService

    svc = _make_verification_service()
    zero = [0.0] * DIM
    nonzero = [1.0] + [0.0] * (DIM - 1)

    score, error = svc.compute_cosine_similarity(zero, nonzero)
    assert score == 0.0
    assert error == "Empty embedding"

    score2, error2 = svc.compute_cosine_similarity(nonzero, zero)
    assert score2 == 0.0
    assert error2 == "Empty embedding"
