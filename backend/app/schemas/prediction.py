from datetime import datetime

from pydantic import BaseModel


class RankedCommand(BaseModel):
    rank: int
    command: str
    confidence: float
    fail_rate_on_similar: str | None = None
    estimated_time_to_fail: str | None = None
    reasoning: str | None = None
    has_feedback: bool = False

    model_config = {"from_attributes": True}


class PredictionOut(BaseModel):
    id: int
    conversation_id: str
    symptom_text: str
    parsed_failure_type: str | None
    parsed_mce_bank: int | None
    parsed_confidence: float | None
    match_tier: int | None
    similar_parts_count: int | None
    model_version: str | None
    created_at: datetime
    commands: list[RankedCommand] = []

    model_config = {"from_attributes": True}


class AccuracyStats(BaseModel):
    total_predictions: int
    total_with_feedback: int
    hit_at_1: float | None = None
    hit_at_3: float | None = None
    hit_at_5: float | None = None
