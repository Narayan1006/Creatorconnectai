from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.services.embedding_service import EmbeddingDimensionMismatchError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    # Initialize and rebuild FAISS index on startup
    from app.services.embedding_service import get_faiss_store, get_embedding_service, embed_and_index_creator
    from app.core.database import get_database
    import os

    # Pre-load embedding model to avoid delay on first profile creation
    embedding_service = get_embedding_service()
    
    faiss_store = get_faiss_store()
    index_file = faiss_store.index_path + ".faiss"

    if os.path.exists(index_file):
        try:
            faiss_store.load()
        except Exception:
            faiss_store.initialize()
    else:
        faiss_store.initialize()

    # Rebuild index from Firestore creators if index is empty
    if faiss_store.count == 0:
        try:
            db = get_database()
            from app.models.creator import Creator
            cursor = db["creators"].find({})
            creators = await cursor.to_list(length=None)
            count = 0
            for doc in creators:
                try:
                    creator = Creator(**doc)
                    embed_and_index_creator(creator, embedding_service, faiss_store)
                    count += 1
                except Exception:
                    continue
            if count > 0:
                faiss_store.save()
        except Exception as e:
            pass  # Non-fatal — matching will return empty until creators are added

    yield
    await close_mongo_connection()


app = FastAPI(
    title="CreatorConnectAI API",
    version="0.1.0",
    description="AI-powered platform connecting businesses with content creators",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EmbeddingDimensionMismatchError)
async def dimension_mismatch_handler(request: Request, exc: EmbeddingDimensionMismatchError):
    return JSONResponse(
        status_code=500,
        content={"error": "Embedding dimension mismatch", "detail": str(exc)},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Router includes
from app.routers import auth, admin, creators, matching, deals
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(creators.router, prefix="/api/creators", tags=["creators"])
app.include_router(matching.router, prefix="/api/match", tags=["matching"])
app.include_router(deals.router, prefix="/api/deals", tags=["deals"])
# app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
