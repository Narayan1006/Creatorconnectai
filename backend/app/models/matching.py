from typing import Annotated

from pydantic import BaseModel, Field

from app.models.creator import CreatorPublic


class MatchQuery(BaseModel):
    product_description: Annotated[str, Field(min_length=10)]
    target_audience: Annotated[str, Field(min_length=5)]
    budget: Annotated[float, Field(gt=0)]
    top_k: Annotated[int, Field(gt=0)] = 5


class RankedCreator(BaseModel):
    creator: CreatorPublic
    match_score: Annotated[float, Field(ge=0.0, le=1.0)]


class MatchResponse(BaseModel):
    results: list[RankedCreator]
    total: int
