"""
Property-based tests for MatchingService.

Property 1 (Req 3.2): result count <= top_k
Property 2 (Req 3.4): scores in [0.0, 1.0]
Property 3 (Req 3.3): results sorted descending by match_score

Uses mock FAISSStore and EmbeddingService — no real models required.
A fixed set of creators is seeded into the mock FAISS index; property
tests run over random MatchQuery inputs.
"""

import sys
import types
import asyncio
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Stub faiss and sentence_transformers before any app import
# ---------------------------------------------------------------------------

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
            def __init__(self, dim: int):
                self.d = dim
                self._data: list[np.ndarray] = []

            def add(self, arr: np.ndarray) -> None:
                self._data.append(arr.copy())

            def search(self, arr: np.ndarray, k: int):
                if not self._data:
                    return np.empty((1, 0)), np.empty((1, 0), dtype=np.int64)
                all_vecs = np.vstack(self._data)
                diffs = all_vecs - arr
                dists = np.sum(diffs ** 2, axis=1).astype(np.float32)
                k_actual = min(k, len(dists))
                idx = np.argsort(dists)[:k_actual]
                return dists[idx].reshape(1, -1), idx.reshape(1, -1).astype(np.int64)

        faiss_mod.IndexFlatL2 = _IndexFlatL2
        sys.modules["faiss"] = faiss_mod


def _stub_motor():
    if "motor" not in sys.modules:
        motor_mod = types.ModuleType("motor")
        motor_async_mod = types.ModuleType("motor.motor_asyncio")

        class _FakeDB:
            pass

        motor_async_mod.AsyncIOMotorClient = MagicMock
        motor_async_mod.AsyncIOMotorDatabase = _FakeDB
        motor_mod.motor_asyncio = motor_async_mod
        sys.modules["motor"] = motor_mod
        sys.modules["motor.motor_asyncio"] = motor_async_mod


_stub_sentence_transformers()
_stub_faiss()
_stub_motor()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIM = 4

# Fixed set of creator IDs seeded into the mock FAISS index
CREATOR_IDS = [f"creator_{i:03d}" for i in range(10)]


def _make_embedding_service(dim: int = DIM) -> "EmbeddingService":
    """Return an EmbeddingService that always produces a zero vector of `dim` dimensions."""
    from app.services.embedding_service import EmbeddingService

    svc = EmbeddingService.__new__(EmbeddingService)
    svc.dimension = dim
    svc._model_type = "local"
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros(dim)
    svc._model = mock_model
    return svc


def _make_faiss_store(creator_ids: list[str], dim: int = DIM) -> "FAISSStore":
    """
    Create a FAISSStore seeded with one vector per creator_id.
    Each creator gets a distinct unit vector so distances are meaningful.
    """
    from app.services.embedding_service import FAISSStore

    store = FAISSStore.__new__(FAISSStore)
    store.index_path = "test_matching"
    store.dimension = dim
    store._index = None
    store._id_map = {}
    store._count = 0
    store.initialize()

    rng = np.random.default_rng(42)
    for creator_id in creator_ids:
        vec = rng.random(dim).astype(np.float32).tolist()
        store.add(creator_id, vec)

    return store


def _make_db(creator_ids: list[str]) -> MagicMock:
    """
    Return a mock AsyncIOMotorDatabase whose find_one returns a minimal
    creator document for any known creator_id, and None for unknown ones.
    """
    from bson import ObjectId

    # Build a lookup of creator_id → ObjectId
    oid_map = {cid: ObjectId() for cid in creator_ids}

    async def _find_one(query, *args, **kwargs):
        # Extract the ObjectId from the query
        oid = query.get("_id")
        # Find matching creator_id
        for cid, stored_oid in oid_map.items():
            if stored_oid == oid:
                return {
                    "_id": stored_oid,
                    "name": f"Creator {cid}",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "niche": ["tech"],
                    "platform": "youtube",
                    "followers": 10000,
                    "engagement_rate": 0.05,
                    "bio": f"Bio for {cid}",
                    "portfolio_url": None,
                }
        return None

    collection_mock = MagicMock()
    collection_mock.find_one = _find_one

    db_mock = MagicMock()
    db_mock.__getitem__ = MagicMock(return_value=collection_mock)
    return db_mock, oid_map


def _make_db_with_str_ids(creator_ids: list[str]) -> MagicMock:
    """
    Return a mock DB where creator_ids stored in FAISS are plain strings
    (not ObjectIds). find_one matches by converting the ObjectId back to str.
    """
    from bson import ObjectId

    async def _find_one(query, *args, **kwargs):
        oid = query.get("_id")
        cid = str(oid)
        # We won't find it — return None to trigger skip logic
        return None

    collection_mock = MagicMock()
    collection_mock.find_one = _find_one

    db_mock = MagicMock()
    db_mock.__getitem__ = MagicMock(return_value=collection_mock)
    return db_mock


def _run(coro):
    """Run a coroutine synchronously (Python 3.10+ compatible)."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Shared fixture: seeded matching service
# ---------------------------------------------------------------------------

def _make_matching_service_with_real_ids():
    """
    Build a MatchingService where FAISS creator_ids are valid ObjectId strings
    so MongoDB find_one can return real documents.
    """
    from bson import ObjectId
    from app.services.matching_service import MatchingService

    # Use real ObjectId strings as creator IDs in FAISS
    oid_strings = [str(ObjectId()) for _ in range(len(CREATOR_IDS))]

    embedding_service = _make_embedding_service()
    faiss_store = _make_faiss_store(oid_strings)

    # Build a DB mock that returns a document for each ObjectId
    async def _find_one(query, *args, **kwargs):
        oid = query.get("_id")
        return {
            "_id": oid,
            "name": f"Creator {str(oid)[:8]}",
            "avatar_url": "https://example.com/avatar.jpg",
            "niche": ["tech"],
            "platform": "youtube",
            "followers": 10000,
            "engagement_rate": 0.05,
            "bio": "A creator bio.",
            "portfolio_url": None,
        }

    collection_mock = MagicMock()
    collection_mock.find_one = _find_one

    db_mock = MagicMock()
    db_mock.__getitem__ = MagicMock(return_value=collection_mock)

    service = MatchingService(
        embedding_service=embedding_service,
        faiss_store=faiss_store,
        db=db_mock,
    )
    return service


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

valid_match_query = st.fixed_dictionaries({
    "product_description": st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))),
    "target_audience": st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))),
    "budget": st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
    "top_k": st.integers(min_value=1, max_value=len(CREATOR_IDS)),
})


# ---------------------------------------------------------------------------
# Property 1: result count <= top_k
# Validates: Requirements 3.2
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(query_data=valid_match_query)
def test_result_count_lte_top_k(query_data):
    """
    Property 1: For any valid MatchQuery with top_k=N, len(results) <= N.

    **Validates: Requirements 3.2**
    """
    from app.models.matching import MatchQuery

    service = _make_matching_service_with_real_ids()
    query = MatchQuery(**query_data)
    results = _run(service.match_creators(query))

    assert len(results) <= query.top_k


# ---------------------------------------------------------------------------
# Property 2: scores in [0.0, 1.0]
# Validates: Requirements 3.4
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(query_data=valid_match_query)
def test_scores_in_unit_interval(query_data):
    """
    Property 2: For any result, 0.0 <= match_score <= 1.0.

    **Validates: Requirements 3.4**
    """
    from app.models.matching import MatchQuery

    service = _make_matching_service_with_real_ids()
    query = MatchQuery(**query_data)
    results = _run(service.match_creators(query))

    for ranked in results:
        assert 0.0 <= ranked.match_score <= 1.0, (
            f"match_score {ranked.match_score} is outside [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# Property 3: results sorted descending by match_score
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(query_data=valid_match_query)
def test_results_sorted_descending(query_data):
    """
    Property 3: scores[i] >= scores[i+1] for all i.

    **Validates: Requirements 3.3**
    """
    from app.models.matching import MatchQuery

    service = _make_matching_service_with_real_ids()
    query = MatchQuery(**query_data)
    results = _run(service.match_creators(query))

    scores = [r.match_score for r in results]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], (
            f"Results not sorted descending at index {i}: "
            f"{scores[i]} < {scores[i + 1]}"
        )
