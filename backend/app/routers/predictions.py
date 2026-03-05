from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.prediction import Prediction, PredictionCommand
from ..schemas.prediction import AccuracyStats, PredictionOut, RankedCommand

router = APIRouter()


@router.get("", response_model=list[PredictionOut])
async def list_predictions(
    limit: int = 50,
    offset: int = 0,
    failure_type: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Prediction).order_by(Prediction.created_at.desc()).limit(limit).offset(offset)

    if failure_type:
        stmt = stmt.where(Prediction.parsed_failure_type == failure_type)

    result = await session.execute(stmt)
    predictions = result.scalars().all()

    out = []
    for pred in predictions:
        cmds_stmt = select(PredictionCommand).where(PredictionCommand.prediction_id == pred.id).order_by(PredictionCommand.rank)
        cmds_result = await session.execute(cmds_stmt)
        cmds = cmds_result.scalars().all()

        out.append(
            PredictionOut(
                id=pred.id,
                conversation_id=pred.conversation_id,
                symptom_text=pred.symptom_text,
                parsed_failure_type=pred.parsed_failure_type,
                parsed_mce_bank=pred.parsed_mce_bank,
                parsed_confidence=pred.parsed_confidence,
                match_tier=pred.match_tier,
                similar_parts_count=pred.similar_parts_count,
                model_version=pred.model_version,
                created_at=pred.created_at,
                commands=[
                    RankedCommand(
                        rank=c.rank,
                        command=c.command,
                        confidence=c.confidence,
                        fail_rate_on_similar=c.fail_rate_on_similar,
                        estimated_time_to_fail=c.estimated_time_to_fail,
                        reasoning=c.reasoning,
                        has_feedback=c.feedback is not None if c.feedback else False,
                    )
                    for c in cmds
                ],
            )
        )

    return out


@router.get("/accuracy", response_model=AccuracyStats)
async def get_accuracy_stats(session: AsyncSession = Depends(get_db)):
    # Placeholder — will be implemented with real feedback data in Phase 4
    return AccuracyStats(
        total_predictions=0,
        total_with_feedback=0,
        hit_at_1=None,
        hit_at_3=None,
        hit_at_5=None,
    )
