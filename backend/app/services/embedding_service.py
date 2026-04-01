import os
import pickle

import numpy as np

from app.core.config import settings


class EmbeddingService:
    """Converts text into vector embeddings using OpenAI or local sentence-transformers."""

    def __init__(self) -> None:
        self.dimension: int = settings.EMBEDDING_DIM

        if settings.EMBEDDING_MODEL == "openai" and settings.OPENAI_API_KEY:
            from langchain_openai import OpenAIEmbeddings
            self._model = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY,
            )
            self._model_type = "openai"
        else:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._model_type = "local"

    def embed(self, text: str) -> list[float]:
        """Embed a text string into a vector."""
        if self._model_type == "openai":
            result = self._model.embed_query(text)
        else:
            result = self._model.encode(text).tolist()

        if len(result) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(result)}"
            )
        return result

    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.dimension


class FAISSStore:
    """FAISS vector index storing creator embeddings."""

    def __init__(self) -> None:
        self.index_path: str = settings.FAISS_INDEX_PATH
        self.dimension: int = settings.EMBEDDING_DIM
        self._index = None
        self._id_map: dict[int, str] = {}
        self._count: int = 0

    def initialize(self) -> None:
        """Create a fresh FAISS flat L2 index."""
        import faiss
        self._index = faiss.IndexFlatL2(self.dimension)
        self._id_map = {}
        self._count = 0

    def add(self, creator_id: str, vector: list[float]) -> None:
        """Add a creator embedding to the index."""
        if self._index is None:
            raise RuntimeError("FAISS index not initialized. Call initialize() first.")
        if len(vector) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )
        arr = np.array(vector, dtype=np.float32).reshape(1, self.dimension)
        self._index.add(arr)
        self._id_map[self._count] = creator_id
        self._count += 1

    def search(self, query_vector: list[float], k: int) -> list[tuple[str, float]]:
        """Search for the k nearest creators. Returns list of (creator_id, l2_distance)."""
        if self._index is None:
            raise RuntimeError("FAISS index not initialized")
        arr = np.array(query_vector, dtype=np.float32).reshape(1, self.dimension)
        distances, indices = self._index.search(arr, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                results.append((self._id_map[int(idx)], float(dist)))
        return results

    @property
    def count(self) -> int:
        """Return the number of vectors in the index."""
        return self._count

    def save(self) -> None:
        """Persist the FAISS index and id_map to disk."""
        import faiss
        faiss.write_index(self._index, self.index_path + ".faiss")
        with open(self.index_path + ".pkl", "wb") as f:
            pickle.dump({"id_map": self._id_map, "count": self._count}, f)

    def load(self) -> None:
        """Load the FAISS index and id_map from disk."""
        import faiss
        self._index = faiss.read_index(self.index_path + ".faiss")
        index_dim = self._index.d
        if index_dim != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: index has {index_dim}, service expects {self.dimension}"
            )
        with open(self.index_path + ".pkl", "rb") as f:
            data = pickle.load(f)
        self._id_map = data["id_map"]
        self._count = data["count"]


class EmbeddingDimensionMismatchError(Exception):
    """Raised when the FAISS index dimension differs from the current embedding service dimension."""
    pass


def detect_dimension_mismatch(faiss_store: "FAISSStore", embedding_service: "EmbeddingService") -> bool:
    """Return True if the loaded FAISS index dimension differs from the embedding service dimension."""
    return (
        faiss_store._index is not None
        and faiss_store._index.d != embedding_service.dimension
    )


def embed_and_index_creator(creator, embedding_service: "EmbeddingService", faiss_store: "FAISSStore") -> list[float]:
    """Build composite text from creator fields, embed it, and add to FAISS index."""
    composite_text = (
        f"Bio: {creator.bio} "
        f"Niche: {' '.join(creator.niche)} "
        f"Platform: {creator.platform}"
    )
    embedding = embedding_service.embed(composite_text)
    faiss_store.add(str(creator.id), embedding)
    return embedding


# Module-level singletons (lazily initialized)
_embedding_service: "EmbeddingService | None" = None
_faiss_store: "FAISSStore | None" = None


def get_embedding_service() -> "EmbeddingService":
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_faiss_store() -> "FAISSStore":
    global _faiss_store
    if _faiss_store is None:
        _faiss_store = FAISSStore()
    return _faiss_store


# Backwards-compatible aliases — resolved on first access
class _LazyProxy:
    """Proxy that forwards attribute access to the real singleton."""

    def __init__(self, factory):
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instance", None)

    def _get(self):
        inst = object.__getattribute__(self, "_instance")
        if inst is None:
            factory = object.__getattribute__(self, "_factory")
            inst = factory()
            object.__setattr__(self, "_instance", inst)
        return inst

    def __getattr__(self, name):
        return getattr(self._get(), name)

    def __setattr__(self, name, value):
        setattr(self._get(), name, value)


embedding_service = _LazyProxy(get_embedding_service)
faiss_store = _LazyProxy(get_faiss_store)
