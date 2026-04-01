from pydantic import BaseModel, Field, model_validator


class VerificationResult(BaseModel):
    deal_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    threshold: float = 0.75
    passed: bool
    feedback: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def compute_passed(cls, values: dict) -> dict:
        if "passed" not in values or values.get("passed") is None:
            score = values.get("match_score", 0.0)
            threshold = values.get("threshold", 0.75)
            values["passed"] = score >= threshold
        return values
