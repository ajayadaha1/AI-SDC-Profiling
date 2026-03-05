from pydantic import BaseModel


class FeedbackSubmission(BaseModel):
    prediction_command_id: int
    actual_result: str  # FAIL, PASS, NOT_RUN
    notes: str | None = None
    submitted_by: str | None = None


class FeedbackOut(BaseModel):
    id: int
    prediction_command_id: int
    actual_result: str
    notes: str | None
    submitted_by: str | None

    model_config = {"from_attributes": True}
