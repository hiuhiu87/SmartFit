from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.training_schema import (
    ExercisePerformanceTrendSchema,
    MuscleFatigueItemSchema,
    TrainingLoadSummarySchema,
    TrainingRecommendationContextSchema,
)

router = APIRouter(prefix="/training", tags=["training"])


@router.get(
    "/context/today",
    response_model=APIResponseSchema[TrainingRecommendationContextSchema],
)
async def get_today_training_context(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TrainingRecommendationContextSchema]:
    result = await container.get_today_training_context_use_case(session).execute(
        user_id
    )
    return APIResponseSchema(
        data=TrainingRecommendationContextSchema(
            recent_load=TrainingLoadSummarySchema(
                **{
                    **asdict(result.recent_load),
                    "user_id": str(result.recent_load.user_id),
                }
            ),
            muscle_fatigue=[
                MuscleFatigueItemSchema(**asdict(item))
                for item in result.muscle_fatigue
            ],
            exercise_trends=[
                ExercisePerformanceTrendSchema(
                    **{**asdict(item), "exercise_id": str(item.exercise_id)}
                )
                for item in result.exercise_trends
            ],
            suggested_focus=result.suggested_focus,
            avoid_focus=result.avoid_focus,
            reason=result.reason,
        )
    )
