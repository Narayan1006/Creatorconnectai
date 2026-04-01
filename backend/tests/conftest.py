"""
Shared pytest fixtures for integration tests.

Provides:
- 20 seeded dummy creators in an in-memory store
- Mocked embedding service (deterministic vectors, DIM=4)
- Mocked FAISS store with those 20 creators indexed
- Business user JWT token / headers
- Creator user JWT token / headers
- TestClient with all dependencies overridden
"""
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies before any app import
# ---------------------------------------------------------------------------

DIM = 4  # test embedding dimension


def _stub_sentence_transformers():
    if "sentence_transformers" not in sys.modules:
        st_mod = types.ModuleType("sentence_transformers")

        class _FakeST:
            def __init__(self, *a, **kw):
                pass

            def encode(self, text):
                return np.zeros(DIM)

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
        faiss_mod.read_index = lambda path: _IndexFlatL2(DIM)
        sys.modules["faiss"] = faiss_mod


def _stub_motor():
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
# 20 dummy creators
# ---------------------------------------------------------------------------

NICHES = [
    ["tech", "gadgets"],
    ["lifestyle", "wellness"],
    ["fitness", "health"],
    ["food", "cooking"],
    ["travel", "adventure"],
    ["fashion", "beauty"],
    ["gaming", "esports"],
    ["finance", "investing"],
    ["education", "science"],
    ["music", "entertainment"],
]

PLATFORMS = ["youtube", "instagram", "tiktok"]


def _make_dummy_creators() -> list[dict]:
    """Return 20 creator dicts with deterministic ObjectIds and embeddings."""
    creators = []
    for i in range(20):
        oid = ObjectId()
        niche = NICHES[i % len(NICHES)]
        platform = PLATFORMS[i % len(PLATFORMS)]
        # Deterministic embedding: [float(i)/20] * DIM
        embedding = [float(i) / 20.0] * DIM
        creators.append(
            {
                "_id": oid,
                "name": f"Creator {i}",
                "avatar_url": f"https://cdn.example.com/avatars/{i}.jpg",
                "niche": niche,
                "platform": platform,
                "followers": 10_000 * (i + 1),
                "engagement_rate": round(0.01 + (i % 10) * 0.009, 4),
                "bio": f"I create {niche[0]} content on {platform}.",
                "portfolio_url": f"https://cdn.example.com/portfolio/{i}",
                "embedding": embedding,
            }
        )
    return creators


# ---------------------------------------------------------------------------
# In-memory DB helpers
# ---------------------------------------------------------------------------

def _make_in_memory_db(initial_creators: list[dict] | None = None):
    """Return (db_mock, stores_dict) where stores_dict has 'creators', 'deals', 'payments'."""
    stores: dict[str, dict] = {
        "creators": {},
        "deals": {},
        "payments": {},
    }

    if initial_creators:
        for c in initial_creators:
            stores["creators"][str(c["_id"])] = dict(c)

    def _make_collection(name: str):
        col = MagicMock()
        store = stores[name]

        async def insert_one(doc):
            doc = dict(doc)
            oid = doc.get("_id") or ObjectId()
            doc["_id"] = oid
            store[str(oid)] = doc
            result = MagicMock()
            result.inserted_id = oid
            return result

        async def find_one(query, *args, **kwargs):
            if "_id" in query:
                return store.get(str(query["_id"]))
            if "deal_id" in query:
                for v in store.values():
                    if v.get("deal_id") == query["deal_id"]:
                        return v
                return None
            return next(iter(store.values()), None) if store else None

        async def update_one(query, update, *args, **kwargs):
            if "_id" in query:
                key = str(query["_id"])
                if key in store:
                    set_vals = update.get("$set", {})
                    store[key].update(set_vals)

        def find(query=None, projection=None, *args, **kwargs):
            cursor = MagicMock()
            docs = list(store.values())

            async def to_list(length=None):
                return docs[:length] if length else docs

            cursor.limit = lambda n: cursor
            cursor.to_list = to_list
            return cursor

        col.insert_one = insert_one
        col.find_one = find_one
        col.update_one = update_one
        col.find = find
        return col

    db = MagicMock()
    _collections = {name: _make_collection(name) for name in stores}

    def _getitem(self, name):
        if name not in _collections:
            _collections[name] = _make_collection(name)
            stores[name] = {}
        return _collections[name]

    db.__getitem__ = _getitem
    return db, stores


def _make_embedding_service(dim: int = DIM):
    svc = MagicMock()
    svc.dimension = dim
    svc.embed.return_value = [0.5] * dim
    return svc


def _make_faiss_store(creators: list[dict], dim: int = DIM):
    """Build a FAISSStore with creators pre-indexed."""
    from app.services.embedding_service import FAISSStore

    store = FAISSStore.__new__(FAISSStore)
    store.index_path = "test_index"
    store.dimension = dim
    store._index = sys.modules["faiss"].IndexFlatL2(dim)
    store._id_map = {}
    store._count = 0

    for i, creator in enumerate(creators):
        vec = np.array(creator["embedding"], dtype=np.float32).reshape(1, dim)
        store._index.add(vec)
        store._id_map[i] = str(creator["_id"])
        store._count += 1

    return store


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _make_business_token() -> str:
    from app.core.auth import create_access_token
    return create_access_token({"sub": "business_user_1", "role": "business"})


def _make_creator_token() -> str:
    from app.core.auth import create_access_token
    return create_access_token({"sub": "creator_user_1", "role": "creator"})


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def dummy_creators() -> list[dict]:
    """20 seeded dummy creator dicts."""
    return _make_dummy_creators()


@pytest.fixture()
def integration_client(dummy_creators):
    """
    TestClient with:
    - 20 seeded creators in in-memory DB + FAISS
    - Mocked embedding service (deterministic DIM=4 vectors)
    - All FastAPI dependencies overridden
    """
    from app.main import app
    from app.core.database import get_database
    from app.services.embedding_service import get_embedding_service, get_faiss_store

    db, stores = _make_in_memory_db(initial_creators=dummy_creators)
    emb_svc = _make_embedding_service(dim=DIM)
    faiss = _make_faiss_store(dummy_creators, dim=DIM)

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_embedding_service] = lambda: emb_svc
    app.dependency_overrides[get_faiss_store] = lambda: faiss

    client = TestClient(app, raise_server_exceptions=False)
    yield client, stores

    app.dependency_overrides.clear()


@pytest.fixture()
def business_headers() -> dict:
    return {"Authorization": f"Bearer {_make_business_token()}"}


@pytest.fixture()
def creator_headers() -> dict:
    return {"Authorization": f"Bearer {_make_creator_token()}"}
