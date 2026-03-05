from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.feedback import Feedback
from ..models.prediction import PredictionCommand
from ..schemas.feedback import FeedbackOut, FeedbackSubmission

router = APIRouter()


@router.post("", response_model=FeedbackOut)
async def submit_feedback(
    body: FeedbackSubmission,
    session: AsyncSession = Depends(get_db),
):
    # Verify the command exists
    cmd = await session.get(PredictionCommand, body.prediction_command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail="Prediction command not found")

    # Check for existing feedback
    if cmd.feedback:
        raise HTTPException(status_code=409, detail="Feedback already submitted for this command")

    fb = Feedback(
        prediction_command_id=body.prediction_command_id,
        actual_result=body.actual_result,
        notes=body.notes,
        submitted_by=body.submitted_by,
    )
    session.add(fb)
    await session.commit()
    await session.refresh(fb)

    return FeedbackOut(
        id=fb.id,
        prediction_command_id=fb.prediction_command_id,
        actual_result=fb.actual_result,
        notes=fb.notes,
        submitted_by=fb.submitted_by,
    )
