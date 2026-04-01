from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # JWT
    JWT_SECRET: str = "change-me-in-production"
    AUTH_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Firebase / Firestore
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_DATABASE_ID: Optional[str] = None  # empty = default database

    # OpenAI (optional)
    OPENAI_API_KEY: Optional[str] = None

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Embedding
    EMBEDDING_MODEL: str = "local"  # "openai" or "local"
    EMBEDDING_DIM: int = 384

    # FAISS
    FAISS_INDEX_PATH: str = "faiss_index"

    # Content URL allowlist (comma-separated domains)
    ALLOWED_CDN_DOMAINS: str = (
        "cdn.example.com,"
        "storage.googleapis.com,"
        "s3.amazonaws.com,"
        "cloudfront.net,"
        "cdn.cloudflare.com,"
        "media.instagram.com,"
        "i.ytimg.com,"
        "pbs.twimg.com"
    )

    # Deal offer limits
    MAX_OFFER_AMOUNT: float = 1_000_000.0
    MIN_OFFER_AMOUNT: float = 1.0

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
