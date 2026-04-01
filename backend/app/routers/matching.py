"""
Matching router — POST /api/match (Business-only)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import require_business
from app.core.database import get_database
from app.models.matching import MatchQuery, MatchResponse
from app.services.embedding_service import (
    EmbeddingService,
    FAISSStore,
    get_embedding_service,
    get_faiss_store,
)
from app.services.matching_service import MatchingService

router = APIRouter()


@router.post("", response_model=MatchResponse)
async def match_creators(
    query: MatchQuery,
    _current_user: dict = Depends(require_business),
    db=Depends(get_database),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    faiss_store: FAISSStore = Depends(get_faiss_store),
):
    service = MatchingService(
        embedding_service=embedding_service,
        faiss_store=faiss_store,
        db=db,
    )

    try:
        results = await service.match_creators(query)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Matching service unavailable", "code": "FAISS_NOT_READY"},
        )

    return MatchResponse(results=results, total=len(results))
