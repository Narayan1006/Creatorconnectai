"""Tests for EmbeddingService (task 4.1)."""
import sys
import types
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Stub out sentence_transformers before any app import so the module-level
# lazy proxy doesn't fail in environments where the package isn't installed.
# ---------------------------------------------------------------------------

def _stub_sentence_transformers():
    if "sentence_transformers" not in sys.modules:
        st_mod = types.ModuleType("sentence_transformers")

        class _FakeST:
            def __init__(self, *a, **kw):
                pass

            def encode(self, text):
                return np.zeros(384)

        st_mod.SentenceTransformer = _FakeST
        sys.modules["sentence_transformers"] = st_mod


def _stub_faiss():
    """Stub faiss with a pure-numpy IndexFlatL2 for testing."""
    if "faiss" not in sys.modules:
        faiss_mod = types.ModuleType("faiss")

        class _IndexFlatL2:
            def __init__(self, dim: int):
                self.d = dim  # faiss uses .d for dimension
                self._data: list[np.ndarray] = []

            def add(self, arr: np.ndarray) -> None:
                self._data.append(arr.copy())

            def search(self, arr: np.ndarray, k: int):
                if not self._data:
                    n = min(k, 0)
                    return np.full((1, n), np.inf), np.full((1, n), -1, dtype=np.int64)
                all_vecs = np.vstack(self._data)
                diffs = all_vecs - arr
                dists = np.sum(diffs ** 2, axis=1)
                k_actual = min(k, len(dists))
                idx = np.argsort(dists)[:k_actual]
                return dists[idx].reshape(1, -1), idx.reshape(1, -1).astype(np.int64)

        def _write_index(index, path):
            import pickle as _pickle
            with open(path, "wb") as f:
                _pickle.dump({"d": index.d}, f)

        def _read_index(path):
            import pickle as _pickle
            with open(path, "rb") as f:
                data = _pickle.load(f)
            idx = _IndexFlatL2(data["d"])
            return idx

        faiss_mod.IndexFlatL2 = _IndexFlatL2
        faiss_mod.write_index = _write_index
        faiss_mod.read_index = _read_index
        sys.modules["faiss"] = faiss_mod


_stub_sentence_transformers()
_stub_faiss()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(model_type: str = "local", dim: int = 384):
    """Instantiate EmbeddingService bypassing __init__, injecting a mock model."""
    from app.services.embedding_service import EmbeddingService

    svc = EmbeddingService.__new__(EmbeddingService)
    svc.dimension = dim
    svc._model_type = model_type

    if model_type == "openai":
        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.1] * dim
        svc._model = mock_model
    else:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * dim)
        svc._model = mock_model

    return svc


# ---------------------------------------------------------------------------
# Unit tests — local model
# ---------------------------------------------------------------------------

class TestEmbeddingServiceLocal:
    def test_get_dimension_returns_configured_dim(self):
        svc = _make_service("local", 384)
        assert svc.get_dimension() == 384

    def test_embed_returns_list_of_floats(self):
        svc = _make_service("local", 384)
        result = svc.embed("hello world")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_embed_returns_correct_length(self):
        svc = _make_service("local", 384)
        result = svc.embed("test text")
        assert len(result) == 384

    def test_embed_calls_encode(self):
        svc = _make_service("local", 384)
        svc.embed("some text")
        svc._model.encode.assert_called_once_with("some text")

    def test_embed_raises_on_dimension_mismatch(self):
        from app.services.embedding_service import EmbeddingService

        svc = EmbeddingService.__new__(EmbeddingService)
        svc.dimension = 384
        svc._model_type = "local"
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * 128)  # wrong dim
        svc._model = mock_model

        with pytest.raises(ValueError, match="dimension mismatch"):
            svc.embed("text")


# ---------------------------------------------------------------------------
# Unit tests — OpenAI model
# ---------------------------------------------------------------------------

class TestEmbeddingServiceOpenAI:
    def test_get_dimension_returns_configured_dim(self):
        svc = _make_service("openai", 1536)
        assert svc.get_dimension() == 1536

    def test_embed_returns_list_of_floats(self):
        svc = _make_service("openai", 1536)
        result = svc.embed("hello world")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_embed_returns_correct_length(self):
        svc = _make_service("openai", 1536)
        result = svc.embed("test text")
        assert len(result) == 1536

    def test_embed_calls_embed_query(self):
        svc = _make_service("openai", 1536)
        svc.embed("some text")
        svc._model.embed_query.assert_called_once_with("some text")

    def test_embed_raises_on_dimension_mismatch(self):
        from app.services.embedding_service import EmbeddingService

        svc = EmbeddingService.__new__(EmbeddingService)
        svc.dimension = 1536
        svc._model_type = "openai"
        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.1] * 512  # wrong dim
        svc._model = mock_model

        with pytest.raises(ValueError, match="dimension mismatch"):
            svc.embed("text")


# ---------------------------------------------------------------------------
# Property-based test
# Validates: Requirements 11.1
# ---------------------------------------------------------------------------

@h_settings(max_examples=50)
@given(text=st.text(min_size=1, max_size=200))
def test_embedding_dimension_consistency(text):
    """
    Property 8: For any text input, the resulting vector must have exactly
    EMBEDDING_DIM dimensions.

    **Validates: Requirements 11.1**
    """
    svc = _make_service("local", 384)
    result = svc.embed(text)
    assert len(result) == 384


# ---------------------------------------------------------------------------
# Helpers for FAISSStore tests
# ---------------------------------------------------------------------------

def _make_faiss_store(dim: int = 4):
    """Create and initialize a FAISSStore with a small dimension for testing."""
    from app.services.embedding_service import FAISSStore

    store = FAISSStore.__new__(FAISSStore)
    store.index_path = "test_faiss_index"
    store.dimension = dim
    store._index = None
    store._id_map = {}
    store._count = 0
    store.initialize()
    return store


def _make_vector(dim: int = 4, value: float = 0.1) -> list[float]:
    return [value] * dim


# ---------------------------------------------------------------------------
# Unit tests — FAISSStore
# ---------------------------------------------------------------------------

class TestFAISSStore:
    def test_initialize_sets_count_to_zero(self):
        store = _make_faiss_store()
        assert store.count == 0

    def test_add_increments_count(self):
        store = _make_faiss_store()
        store.add("creator_1", _make_vector())
        assert store.count == 1

    def test_add_multiple_increments_count(self):
        store = _make_faiss_store()
        store.add("creator_1", _make_vector(value=0.1))
        store.add("creator_2", _make_vector(value=0.2))
        store.add("creator_3", _make_vector(value=0.3))
        assert store.count == 3

    def test_add_raises_on_wrong_dimension(self):
        store = _make_faiss_store(dim=4)
        with pytest.raises(ValueError, match="dimension mismatch"):
            store.add("creator_1", [0.1, 0.2])  # wrong dim

    def test_search_returns_correct_creator(self):
        store = _make_faiss_store(dim=4)
        store.add("creator_abc", [1.0, 0.0, 0.0, 0.0])
        store.add("creator_xyz", [0.0, 1.0, 0.0, 0.0])
        results = store.search([1.0, 0.0, 0.0, 0.0], k=1)
        assert len(results) == 1
        assert results[0][0] == "creator_abc"

    def test_search_returns_tuple_of_id_and_distance(self):
        store = _make_faiss_store(dim=4)
        store.add("creator_1", [1.0, 0.0, 0.0, 0.0])
        results = store.search([1.0, 0.0, 0.0, 0.0], k=1)
        creator_id, distance = results[0]
        assert isinstance(creator_id, str)
        assert isinstance(distance, float)

    def test_search_exact_match_has_zero_distance(self):
        store = _make_faiss_store(dim=4)
        vec = [0.5, 0.5, 0.5, 0.5]
        store.add("creator_exact", vec)
        results = store.search(vec, k=1)
        assert results[0][1] == pytest.approx(0.0, abs=1e-5)

    def test_id_map_stores_creator_ids(self):
        store = _make_faiss_store(dim=4)
        store.add("creator_a", _make_vector(value=0.1))
        store.add("creator_b", _make_vector(value=0.2))
        assert store._id_map[0] == "creator_a"
        assert store._id_map[1] == "creator_b"


# ---------------------------------------------------------------------------
# Unit tests — embed_and_index_creator
# ---------------------------------------------------------------------------

class TestEmbedAndIndexCreator:
    def _make_creator(self, bio="Tech enthusiast", niche=None, platform="youtube", creator_id="abc123"):
        """Build a minimal creator-like object."""
        from unittest.mock import MagicMock
        creator = MagicMock()
        creator.id = creator_id
        creator.bio = bio
        creator.niche = niche or ["tech", "lifestyle"]
        creator.platform = platform
        return creator

    def test_returns_embedding_vector(self):
        from app.services.embedding_service import embed_and_index_creator

        svc = _make_service("local", 4)
        svc._model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        store = _make_faiss_store(dim=4)
        creator = self._make_creator()

        result = embed_and_index_creator(creator, svc, store)
        assert isinstance(result, list)
        assert len(result) == 4

    def test_increments_faiss_count_by_one(self):
        from app.services.embedding_service import embed_and_index_creator

        svc = _make_service("local", 4)
        svc._model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        store = _make_faiss_store(dim=4)
        creator = self._make_creator()

        before = store.count
        embed_and_index_creator(creator, svc, store)
        assert store.count == before + 1

    def test_stores_creator_id_in_index(self):
        from app.services.embedding_service import embed_and_index_creator

        svc = _make_service("local", 4)
        svc._model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        store = _make_faiss_store(dim=4)
        creator = self._make_creator(creator_id="creator_999")

        embed_and_index_creator(creator, svc, store)
        assert store._id_map[0] == "creator_999"

    def test_composite_text_format(self):
        from app.services.embedding_service import embed_and_index_creator

        svc = _make_service("local", 4)
        svc._model.encode.return_value = np.array([0.1, 0.2, 0.3, 0.4])
        store = _make_faiss_store(dim=4)
        creator = self._make_creator(bio="Fitness coach", niche=["fitness", "health"], platform="instagram")

        embed_and_index_creator(creator, svc, store)
        call_text = svc._model.encode.call_args[0][0]
        assert "Bio: Fitness coach" in call_text
        assert "Niche: fitness health" in call_text
        assert "Platform: instagram" in call_text


# ---------------------------------------------------------------------------
# Property-based test — FAISS count increments by 1
# Validates: Requirements 2.5, 2.6
# ---------------------------------------------------------------------------

@h_settings(max_examples=30)
@given(
    creator_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    values=st.lists(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=4, max_size=4),
)
def test_faiss_count_increments_by_one(creator_id, values):
    """
    Property 12: For any creator indexed, the FAISS store count increases by exactly 1.

    **Validates: Requirements 2.5, 2.6**
    """
    store = _make_faiss_store(dim=4)
    before = store.count
    store.add(creator_id, values)
    assert store.count == before + 1


# ---------------------------------------------------------------------------
# Unit tests — FAISSStore dimension mismatch and uninitialized guards (task 4.5)
# ---------------------------------------------------------------------------

class TestFAISSStoreDimensionMismatch:
    def test_add_raises_runtime_error_when_index_not_initialized(self):
        from app.services.embedding_service import FAISSStore

        store = FAISSStore.__new__(FAISSStore)
        store.index_path = "test_faiss_index"
        store.dimension = 4
        store._index = None
        store._id_map = {}
        store._count = 0

        with pytest.raises(RuntimeError, match="FAISS index not initialized. Call initialize\\(\\) first\\."):
            store.add("creator_1", [0.1, 0.2, 0.3, 0.4])

    def test_search_raises_runtime_error_when_index_not_initialized(self):
        from app.services.embedding_service import FAISSStore

        store = FAISSStore.__new__(FAISSStore)
        store.index_path = "test_faiss_index"
        store.dimension = 4
        store._index = None
        store._id_map = {}
        store._count = 0

        with pytest.raises(RuntimeError, match="FAISS index not initialized"):
            store.search([0.1, 0.2, 0.3, 0.4], k=1)

    def test_load_raises_value_error_on_dimension_mismatch(self, tmp_path):
        import faiss
        import pickle
        from unittest.mock import patch, MagicMock

        # Create a mock index that reports dim=8
        mock_index = MagicMock()
        mock_index.d = 8

        index_path = str(tmp_path / "mismatch_index")
        with open(index_path + ".pkl", "wb") as f:
            pickle.dump({"id_map": {}, "count": 0}, f)

        from app.services.embedding_service import FAISSStore

        store = FAISSStore.__new__(FAISSStore)
        store.index_path = index_path
        store.dimension = 4  # different from saved index dim (8)
        store._index = None
        store._id_map = {}
        store._count = 0

        with patch("faiss.read_index", return_value=mock_index):
            with pytest.raises(ValueError, match="Embedding dimension mismatch: index has 8, service expects 4"):
                store.load()

    def test_load_succeeds_when_dimensions_match(self, tmp_path):
        import faiss
        import pickle

        index = faiss.IndexFlatL2(4)
        index_path = str(tmp_path / "match_index")
        faiss.write_index(index, index_path + ".faiss")
        with open(index_path + ".pkl", "wb") as f:
            pickle.dump({"id_map": {}, "count": 0}, f)

        from app.services.embedding_service import FAISSStore

        store = FAISSStore.__new__(FAISSStore)
        store.index_path = index_path
        store.dimension = 4
        store._index = None
        store._id_map = {}
        store._count = 0

        store.load()  # should not raise
        assert store._index is not None


class TestDetectDimensionMismatch:
    def test_returns_false_when_index_is_none(self):
        from app.services.embedding_service import detect_dimension_mismatch, FAISSStore, EmbeddingService

        store = FAISSStore.__new__(FAISSStore)
        store._index = None
        store.dimension = 384

        svc = EmbeddingService.__new__(EmbeddingService)
        svc.dimension = 384

        assert detect_dimension_mismatch(store, svc) is False

    def test_returns_false_when_dimensions_match(self):
        from app.services.embedding_service import detect_dimension_mismatch, FAISSStore, EmbeddingService
        import faiss

        store = FAISSStore.__new__(FAISSStore)
        store._index = faiss.IndexFlatL2(384)
        store.dimension = 384

        svc = EmbeddingService.__new__(EmbeddingService)
        svc.dimension = 384

        assert detect_dimension_mismatch(store, svc) is False

    def test_returns_true_when_dimensions_differ(self):
        from app.services.embedding_service import detect_dimension_mismatch, FAISSStore, EmbeddingService
        import faiss

        store = FAISSStore.__new__(FAISSStore)
        store._index = faiss.IndexFlatL2(1536)  # index built with OpenAI dim
        store.dimension = 1536

        svc = EmbeddingService.__new__(EmbeddingService)
        svc.dimension = 384  # service now uses local model

        assert detect_dimension_mismatch(store, svc) is True
