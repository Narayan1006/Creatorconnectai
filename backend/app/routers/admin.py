from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.core.database import get_database
from app.models.creator import Creator
from app.services.embedding_service import (
    embed_and_index_creator,
    get_embedding_service,
    get_faiss_store,
    EmbeddingService,
    FAISSStore,
)

router = APIRouter()


@router.post("/reindex")
async def reindex(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    faiss_store: FAISSStore = Depends(get_faiss_store),
):
    """Re-embed all creator profiles and rebuild the FAISS index."""
    cursor = db["creators"].find({})
    creators = await cursor.to_list(length=None)

    faiss_store.initialize()

    count = 0
    for doc in creators:
        creator = Creator(**doc)
        embed_and_index_creator(creator, embedding_service, faiss_store)
        count += 1

    faiss_store.save()
    return {"reindexed": count, "message": "Reindex complete"}
