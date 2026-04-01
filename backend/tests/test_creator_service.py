"""
Property-based tests for Creator profile service.

Property 7  (Req 2.2):  engagement_rate outside [0,1] → POST /api/creators returns 422
Property 13 (Req 10.3): GET /api/creators/featured response dicts have no "embedding" key
"""
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Stub heavy optional dependencies before any app import
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
                self._data: list = []

            def add(self, arr) -> None:
                self._data.append(arr.copy())

            def search(self, arr, k: int):
                n = min(k, len(self._data))
                return np.zeros((1, n)), np.arange(n, dtype=np.int64).reshape(1, n)

        faiss_mod.IndexFlatL2 = _IndexFlatL2
        faiss_mod.write_index = lambda idx, path: None
        faiss_mod.read_index = lambda path: _IndexFlatL2(4)
        sys.modules["faiss"] = faiss_mod


def _stub_motor():
    """Stub motor.motor_asyncio so app.core.database can be imported without MongoDB."""
    if "motor" not in sys.modules:
        motor_mod = types.ModuleType("motor")
        motor_asyncio = types.ModuleType("motor.motor_asyncio")

        class _FakeClient:
            def __init__(self, *a, **kw):
                pass

            def __getitem__(self, name):
                return MagicMock()

            def close(self):
                pass

        class _FakeDatabase:
            pass

        motor_asyncio.AsyncIOMotorClient = _FakeClient
        motor_asyncio.AsyncIOMotorDatabase = _FakeDatabase
        motor_mod.motor_asyncio = motor_asyncio
        sys.modules["motor"] = motor_mod
        sys.modules["motor.motor_asyncio"] = motor_asyncio


_stub_sentence_transformers()
_stub_faiss()
_stub_motor()


# ---------------------------------------------------------------------------
# In-memory MongoDB mock helpers
# ---------------------------------------------------------------------------

def _make_in_memory_db():
    """Return a mock AsyncIOMotorDatabase backed by a plain dict."""
    store: dict[str, dict] = {}
    db = MagicMock()

    collection = MagicMock()

    async def insert_one(doc):
        from bson import ObjectId
        oid = ObjectId()
        doc = dict(doc)
        doc["_id"] = oid
        store[str(oid)] = doc
        result = MagicMock()
        result.inserted_id = oid
        return result

    async def find_one(query, *args, **kwargs):
        from bson import ObjectId
        if "_id" in query:
            oid = query["_id"]
            return store.get(str(oid))
        return next(iter(store.values()), None) if store else None

    async def update_one(query, update, *args, **kwargs):
        from bson import ObjectId
        if "_id" in query:
            oid = str(query["_id"])
            if oid in store:
                set_vals = update.get("$set", {})
                store[oid].update(set_vals)

    # Cursor mock for find()
    def find(query=None, projection=None, *args, **kwargs):
        cursor = MagicMock()
        docs = list(store.values())
        
        # Apply projection if specified (e.g., {"embedding": 0} to exclude embedding)
        if projection:
            filtered_docs = []
            for doc in docs:
                doc_copy = dict(doc)
                for key, value in projection.items():
                    if value == 0 and key in doc_copy:
                        doc_copy.pop(key)
                filtered_docs.append(doc_copy)
            docs = filtered_docs

        async def to_list(length=None):
            return docs[:length] if length else docs

        def limit(n):
            # Return a new cursor-like object that limits results
            limited_cursor = MagicMock()
            limited_cursor.to_list = lambda length=None: to_list(n)
            return limited_cursor

        cursor.limit = limit
        cursor.to_list = to_list
        return cursor

    collection.insert_one = insert_one
    collection.find_one = find_one
    collection.update_one = update_one
    collection.find = find

    db.__getitem__ = lambda self, name: collection
    return db, store


def _make_embedding_service(dim: int = 4):
    """Return a mock EmbeddingService that returns a fixed-dim vector."""
    svc = MagicMock()
    svc.dimension = dim
    svc.embed.return_value = [0.1] * dim
    return svc


def _make_faiss_store(dim: int = 4):
    """Return a mock FAISSStore."""
    from app.services.embedding_service import FAISSStore
    store = FAISSStore.__new__(FAISSStore)
    store.index_path = "test_index"
    store.dimension = dim
    store._index = sys.modules["faiss"].IndexFlatL2(dim)
    store._id_map = {}
    store._count = 0
    return store


# ---------------------------------------------------------------------------
# App fixture with overridden dependencies
# ---------------------------------------------------------------------------

def _build_test_client():
    """Build a TestClient with all heavy dependencies mocked out."""
    from app.main import app
    from app.core.database import get_database
    from app.services.embedding_service import get_embedding_service, get_faiss_store

    db, store = _make_in_memory_db()
    emb_svc = _make_embedding_service(dim=4)
    faiss = _make_faiss_store(dim=4)

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_embedding_service] = lambda: emb_svc
    app.dependency_overrides[get_faiss_store] = lambda: faiss

    client = TestClient(app, raise_server_exceptions=False)
    return client, store, app


# ---------------------------------------------------------------------------
# JWT helper — create a valid creator token for auth
# ---------------------------------------------------------------------------

def _creator_auth_headers():
    from app.core.auth import create_access_token
    token = create_access_token({"sub": "creator_user", "role": "creator"})
    return {"Authorization": f"Bearer {token}"}


def _valid_creator_payload(**overrides):
    base = {
        "name": "Test Creator",
        "avatar_url": "https://example.com/avatar.jpg",
        "niche": ["tech"],
        "platform": "youtube",
        "followers": 10000,
        "engagement_rate": 0.05,
        "bio": "A tech creator",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Property 7: engagement_rate outside [0,1] → POST /api/creators returns 422
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------

@h_settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    bad_rate=st.one_of(
        st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False),
        st.floats(min_value=1.0001, allow_nan=False, allow_infinity=False),
    )
)
def test_property_7_invalid_engagement_rate_returns_422(bad_rate):
    """
    Property 7: For any creator with engagement_rate outside [0, 1],
    POST /api/creators must return HTTP 422.

    **Validates: Requirements 2.2**
    """
    client, _, app = _build_test_client()
    payload = _valid_creator_payload(engagement_rate=bad_rate)
    response = client.post(
        "/api/creators",
        json=payload,
        headers=_creator_auth_headers(),
    )
    assert response.status_code == 422, (
        f"Expected 422 for engagement_rate={bad_rate}, got {response.status_code}"
    )
    # Clean up overrides
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Property 13: GET /api/creators/featured response has no "embedding" key
# Validates: Requirements 10.3
# ---------------------------------------------------------------------------

@h_settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    num_creators=st.integers(min_value=0, max_value=10),
)
def test_property_13_featured_response_excludes_embedding(num_creators):
    """
    Property 13: For any number of creators in the store, every item returned
    by GET /api/creators/featured must NOT contain an "embedding" key.

    **Validates: Requirements 10.3**
    """
    from app.main import app
    from app.core.database import get_database
    from app.services.embedding_service import get_embedding_service, get_faiss_store
    from bson import ObjectId

    db, store = _make_in_memory_db()
    emb_svc = _make_embedding_service(dim=4)
    faiss = _make_faiss_store(dim=4)

    # Pre-populate the in-memory store with creators that have embeddings
    for i in range(num_creators):
        oid = ObjectId()
        store[str(oid)] = {
            "_id": oid,
            "name": f"Creator {i}",
            "avatar_url": f"https://example.com/{i}.jpg",
            "niche": ["tech"],
            "platform": "youtube",
            "followers": 1000 + i,
            "engagement_rate": 0.05,
            "bio": f"Bio {i}",
            "portfolio_url": None,
            "embedding": [0.1, 0.2, 0.3, 0.4],  # should be stripped from response
        }

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_embedding_service] = lambda: emb_svc
    app.dependency_overrides[get_faiss_store] = lambda: faiss

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/creators/featured")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    creators = response.json()
    assert isinstance(creators, list)
    assert len(creators) <= 10

    for creator in creators:
        assert "embedding" not in creator, (
            f"'embedding' key found in featured creator response: {creator}"
        )

    app.dependency_overrides.clear()
