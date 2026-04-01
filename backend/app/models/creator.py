from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.models.base import BaseDocument


class Creator(BaseDocument):
    name: str
    avatar_url: str
    niche: list[str]
    platform: str  # "instagram" | "youtube" | "tiktok"
    followers: int
    engagement_rate: float
    bio: str
    portfolio_url: Optional[str] = None
    embedding: Optional[list[float]] = None

    @field_validator("niche")
    @classmethod
    def niche_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("niche must contain at least one entry")
        return v

    @field_validator("followers")
    @classmethod
    def followers_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("followers must be a positive integer (> 0)")
        return v

    @field_validator("engagement_rate")
    @classmethod
    def engagement_rate_must_be_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("engagement_rate must be between 0.0 and 1.0")
        return v


class CreatorCreate(BaseModel):
    name: str
    avatar_url: str
    niche: list[str]
    platform: str
    followers: int
    engagement_rate: float
    bio: str
    portfolio_url: Optional[str] = None
    embedding: Optional[list[float]] = None

    @field_validator("niche")
    @classmethod
    def niche_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("niche must contain at least one entry")
        return v

    @field_validator("followers")
    @classmethod
    def followers_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("followers must be a positive integer (> 0)")
        return v

    @field_validator("engagement_rate")
    @classmethod
    def engagement_rate_must_be_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("engagement_rate must be between 0.0 and 1.0")
        return v


class CreatorUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    niche: Optional[list[str]] = None
    platform: Optional[str] = None
    followers: Optional[int] = None
    engagement_rate: Optional[float] = None
    bio: Optional[str] = None
    portfolio_url: Optional[str] = None
    embedding: Optional[list[float]] = None

    @field_validator("niche")
    @classmethod
    def niche_must_not_be_empty(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and not v:
            raise ValueError("niche must contain at least one entry")
        return v

    @field_validator("followers")
    @classmethod
    def followers_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("followers must be a positive integer (> 0)")
        return v

    @field_validator("engagement_rate")
    @classmethod
    def engagement_rate_must_be_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("engagement_rate must be between 0.0 and 1.0")
        return v


class CreatorPublic(BaseModel):
    """Public-facing Creator model — excludes the embedding field."""

    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    avatar_url: Optional[str] = ""
    niche: list[str]
    platform: str
    followers: int
    engagement_rate: float
    bio: str
    portfolio_url: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }
