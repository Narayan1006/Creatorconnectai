"""
Firestore database layer.

Provides a thin async wrapper around google-cloud-firestore that mirrors
the Motor/MongoDB collection API used throughout the app:

    db["collection"].find_one(query)
    db["collection"].find(query)          → cursor with .to_list()
    db["collection"].insert_one(doc)      → result with .inserted_id
    db["collection"].update_one(filter, update)
    db["collection"].delete_one(filter)

Documents use string IDs (Firestore document IDs) stored as "_id".
"""

import os
from typing import Any, Optional
from app.core.config import settings

_db = None  # google.cloud.firestore.AsyncClient


async def connect_to_mongo() -> None:
    """Initialize Firestore client (called at startup)."""
    global _db
    import firebase_admin
    from firebase_admin import credentials, firestore_async

    if not firebase_admin._apps:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Fall back to application default credentials
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {
            "projectId": settings.FIREBASE_PROJECT_ID,
        })

    _db = firestore_async.client()


async def close_mongo_connection() -> None:
    """No-op for Firestore (connections are managed by the SDK)."""
    pass


def get_database() -> "FirestoreDatabase":
    if _db is None:
        raise RuntimeError("Firestore client not initialized. Call connect_to_mongo() first.")
    return FirestoreDatabase(_db)


# ---------------------------------------------------------------------------
# Firestore ↔ Motor compatibility shim
# ---------------------------------------------------------------------------

class InsertResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class FirestoreCursor:
    """Mimics Motor cursor with .to_list()."""

    def __init__(self, docs: list[dict]):
        self._docs = docs

    def limit(self, n: int) -> "FirestoreCursor":
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length: Optional[int] = None) -> list[dict]:
        if length is not None:
            return self._docs[:length]
        return self._docs


class FirestoreCollection:
    """Async collection wrapper that mirrors Motor's AsyncIOMotorCollection API."""

    def __init__(self, col_ref):
        self._col = col_ref

    # ------------------------------------------------------------------
    # find_one
    # ------------------------------------------------------------------

    async def find_one(self, query: dict, *args, **kwargs) -> Optional[dict]:
        """Return the first document matching query, or None."""
        # Direct ID lookup
        if "_id" in query and len(query) == 1:
            doc_ref = self._col.document(str(query["_id"]))
            snap = await doc_ref.get()
            if snap.exists:
                data = snap.to_dict()
                data["_id"] = snap.id
                return data
            return None

        # Field query — fetch all and filter in Python
        docs = await self._fetch_all_matching(query)
        return docs[0] if docs else None

    # ------------------------------------------------------------------
    # find  (returns cursor)
    # ------------------------------------------------------------------

    def find(self, query: Optional[dict] = None, projection: Optional[dict] = None,
             *args, **kwargs) -> FirestoreCursor:
        """Return a cursor over matching documents (evaluated lazily via to_list)."""
        import asyncio

        async def _fetch():
            return await self._fetch_all_matching(query or {})

        # We need to return a cursor synchronously but fetch async.
        # Use a lazy cursor that fetches on to_list().
        return _LazyFirestoreCursor(self._col, query or {}, projection)

    # ------------------------------------------------------------------
    # insert_one
    # ------------------------------------------------------------------

    async def insert_one(self, doc: dict) -> InsertResult:
        """Insert a document. Uses doc["_id"] if present, else auto-generates."""
        import uuid
        doc = dict(doc)
        doc_id = str(doc.pop("_id", None) or uuid.uuid4().hex)
        # Convert non-serializable types
        doc = _prepare_for_firestore(doc)
        await self._col.document(doc_id).set(doc)
        return InsertResult(doc_id)

    # ------------------------------------------------------------------
    # update_one
    # ------------------------------------------------------------------

    async def update_one(self, filter_: dict, update: dict, *args, **kwargs) -> None:
        """Update the first matching document."""
        doc = await self.find_one(filter_)
        if doc is None:
            return
        doc_id = str(doc["_id"])
        if "$set" in update:
            data = _prepare_for_firestore(dict(update["$set"]))
            await self._col.document(doc_id).update(data)
        elif "$unset" in update:
            from google.cloud.firestore import DELETE_FIELD
            data = {k: DELETE_FIELD for k in update["$unset"]}
            await self._col.document(doc_id).update(data)

    # ------------------------------------------------------------------
    # delete_one
    # ------------------------------------------------------------------

    async def delete_one(self, filter_: dict) -> None:
        doc = await self.find_one(filter_)
        if doc:
            await self._col.document(str(doc["_id"])).delete()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_all_matching(self, query: dict) -> list[dict]:
        """Fetch docs using Firestore where clauses for indexed fields, fallback to scan."""
        from google.cloud.firestore import AsyncCollectionReference

        # Use native Firestore where() for simple equality queries
        if query and all(k not in ('_id',) for k in query):
            try:
                ref = self._col
                for key, value in query.items():
                    ref = ref.where(key, '==', value)
                results = []
                async for snap in ref.stream():
                    data = snap.to_dict()
                    data['_id'] = snap.id
                    results.append(data)
                return results
            except Exception:
                pass  # fall through to scan

        # Full scan fallback
        snaps = self._col.stream()
        results = []
        async for snap in snaps:
            data = snap.to_dict()
            data['_id'] = snap.id
            if _matches(data, query):
                results.append(data)
        return results


class _LazyFirestoreCursor:
    """Cursor that fetches from Firestore on to_list()."""

    def __init__(self, col_ref, query: dict, projection: Optional[dict]):
        self._col = col_ref
        self._query = query
        self._projection = projection
        self._limit_n: Optional[int] = None

    def limit(self, n: int) -> "_LazyFirestoreCursor":
        self._limit_n = n
        return self

    async def to_list(self, length: Optional[int] = None) -> list[dict]:
        snaps = self._col.stream()
        results = []
        async for snap in snaps:
            data = snap.to_dict()
            data["_id"] = snap.id
            if _matches(data, self._query):
                # Apply projection: exclude fields with value 0
                if self._projection:
                    for field, val in self._projection.items():
                        if val == 0:
                            data.pop(field, None)
                results.append(data)

        cap = length or self._limit_n
        if cap is not None:
            results = results[:cap]
        return results


class FirestoreDatabase:
    """Mimics AsyncIOMotorDatabase — access collections via db["name"]."""

    def __init__(self, client):
        self._client = client

    def __getitem__(self, collection_name: str) -> FirestoreCollection:
        return FirestoreCollection(self._client.collection(collection_name))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _matches(doc: dict, query: dict) -> bool:
    """Simple equality filter (supports top-level fields and deal_id)."""
    for key, value in query.items():
        if key == "_id":
            if str(doc.get("_id", "")) != str(value):
                return False
        elif doc.get(key) != value:
            return False
    return True


def _prepare_for_firestore(data: dict) -> dict:
    """Convert Python types that Firestore can't handle natively."""
    from datetime import datetime
    result = {}
    for k, v in data.items():
        if hasattr(v, "hex") and callable(v.hex):  # ObjectId-like
            result[k] = str(v)
        elif isinstance(v, dict):
            result[k] = _prepare_for_firestore(v)
        elif isinstance(v, list):
            result[k] = [
                _prepare_for_firestore(i) if isinstance(i, dict) else
                str(i) if hasattr(i, "hex") and callable(getattr(i, "hex", None)) else i
                for i in v
            ]
        else:
            result[k] = v
    return result
