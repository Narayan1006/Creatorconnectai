from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class BaseDocument(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_timezone(cls, v: Any) -> datetime:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
