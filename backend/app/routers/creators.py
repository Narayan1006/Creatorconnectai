"""
Creator profile CRUD endpoints.

Routes
------
POST   /api/creators            — Creator-only, create a new profile
GET    /api/creators/featured   — Public, returns up to 10 creators (no embedding)
GET    /api/creators/{id}       — Authenticated, returns a single creator (no embedding)
PUT    /api/creators/{id}       — Creator-only, update own profile
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user, require_creator
from app.core.database import get_database
from app.models.creator import Creator, CreatorCreate, CreatorUpdate, CreatorPublic
from app.services.embedding_service import (
    embed_and_index_creator,
    get_embedding_service,
    get_faiss_store,
    EmbeddingService,
    FAISSStore,
)

router = APIRouter()


def _doc_to_public(doc: dict) -> CreatorPublic:
    doc = dict(doc)
    doc.pop("embedding", None)
    # Convert ObjectId to string if present
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    # Firestore may return niche as a string — normalize to list
    if isinstance(doc.get("niche"), str):
        doc["niche"] = [n.strip() for n in doc["niche"].split(",") if n.strip()]
    # avatar_url is optional in public view
    doc.setdefault("avatar_url", "")
    return CreatorPublic(**doc)


# ---------------------------------------------------------------------------
# GET /me  — returns the current creator's own profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=CreatorPublic)
async def get_my_creator_profile(
    current_user: dict = Depends(require_creator),
    db=Depends(get_database),
):
    """Return the creator profile for the currently logged-in creator."""
    user_id = current_user.get("sub", "")
    all_docs = await db["creators"].find({}).to_list(length=500)
    for doc in all_docs:
        if doc.get("user_id") == user_id:
            return _doc_to_public(doc)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator profile not found")


@router.post("/me/link/{profile_id}", response_model=CreatorPublic)
async def link_creator_profile(
    profile_id: str,
    current_user: dict = Depends(require_creator),
    db=Depends(get_database),
):
    """Link an existing creator profile to the current logged-in user."""
    user_id = current_user.get("sub", "")
    doc = await db["creators"].find_one({"_id": profile_id})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await db["creators"].update_one({"_id": profile_id}, {"$set": {"user_id": user_id}})
    updated = await db["creators"].find_one({"_id": profile_id})
    return _doc_to_public(updated)


# ---------------------------------------------------------------------------
# GET /featured  — public, no auth required
# MUST be declared before /{creator_id}
# ---------------------------------------------------------------------------

@router.get("/featured", response_model=list[CreatorPublic])
async def get_featured_creators(db=Depends(get_database)):
    cursor = db["creators"].find({}, {"embedding": 0}).limit(10)
    docs = await cursor.to_list(length=10)
    return [_doc_to_public(doc) for doc in docs]


# ---------------------------------------------------------------------------
# POST /  — Creator-only
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreatorPublic)
async def create_creator(
    payload: CreatorCreate,
    current_user: dict = Depends(require_creator),
    db=Depends(get_database),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    faiss_store: FAISSStore = Depends(get_faiss_store),
):
    now = datetime.now(timezone.utc)
    creator_id = uuid.uuid4().hex
    doc = payload.model_dump()
    doc["_id"] = creator_id
    doc["user_id"] = current_user.get("sub", "")  # link creator profile to auth user
    doc["created_at"] = now
    doc["updated_at"] = now

    await db["creators"].insert_one(doc)

    # Fetch back and embed
    raw = await db["creators"].find_one({"_id": creator_id})
    creator = Creator(**raw)
    embedding = embed_and_index_creator(creator, embedding_service, faiss_store)
    
    # Persist FAISS index to disk
    faiss_store.save()

    await db["creators"].update_one({"_id": creator_id}, {"$set": {"embedding": embedding}})

    updated = await db["creators"].find_one({"_id": creator_id})
    return _doc_to_public(updated)


# ---------------------------------------------------------------------------
# GET /{creator_id}  — authenticated
# ---------------------------------------------------------------------------

@router.get("/{creator_id}", response_model=CreatorPublic)
async def get_creator(
    creator_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    doc = await db["creators"].find_one({"_id": creator_id})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator not found")
    return _doc_to_public(doc)


# ---------------------------------------------------------------------------
# PUT /{creator_id}  — Creator-only
# ---------------------------------------------------------------------------

@router.put("/{creator_id}", response_model=CreatorPublic)
async def update_creator(
    creator_id: str,
    payload: CreatorUpdate,
    current_user: dict = Depends(require_creator),
    db=Depends(get_database),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    faiss_store: FAISSStore = Depends(get_faiss_store),
):
    existing = await db["creators"].find_one({"_id": creator_id})
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    await db["creators"].update_one({"_id": creator_id}, {"$set": updates})

    raw = await db["creators"].find_one({"_id": creator_id})
    creator = Creator(**raw)
    embedding = embed_and_index_creator(creator, embedding_service, faiss_store)
    
    # Persist FAISS index to disk
    faiss_store.save()
    
    await db["creators"].update_one({"_id": creator_id}, {"$set": {"embedding": embedding}})

    final = await db["creators"].find_one({"_id": creator_id})
    return _doc_to_public(final)
