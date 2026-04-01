"""
MatchingService — RAG-based creator matching using FAISS + Firestore.
"""

from __future__ import annotations

from app.models.creator import CreatorPublic
from app.models.matching import MatchQuery, RankedCreator
from app.services.embedding_service import EmbeddingService, FAISSStore


class MatchingService:
    def __init__(self, embedding_service: EmbeddingService, faiss_store: FAISSStore, db) -> None:
        self._embedding_service = embedding_service
        self._faiss_store = faiss_store
        self._db = db

    async def match_creators(self, query: MatchQuery) -> list[RankedCreator]:
        query_text = (
            f"Product: {query.product_description} "
            f"Audience: {query.target_audience} "
            f"Budget: {query.budget}"
        )

        query_vector = self._embedding_service.embed(query_text)
        raw_results = self._faiss_store.search(query_vector, query.top_k)

        ranked: list[RankedCreator] = []
        for creator_id, l2_distance in raw_results:
            match_score = 1.0 / (1.0 + l2_distance)

            doc = await self._db["creators"].find_one({"_id": creator_id})
            if doc is None:
                continue

            doc.pop("embedding", None)
            # Convert ObjectId to string if present
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            creator_public = CreatorPublic(**doc)
            ranked.append(RankedCreator(creator=creator_public, match_score=match_score))

        ranked.sort(key=lambda r: r.match_score, reverse=True)
        return ranked
