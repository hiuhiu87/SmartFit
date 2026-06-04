from dataclasses import asdict
from datetime import date as date_type
from uuid import UUID

from src.application.training.dto import (
    ExercisePerformanceTrendDTO,
    MuscleFatigueItemDTO,
    TrainingLoadSummaryDTO,
    TrainingRecommendationContextDTO,
)
from src.domain.training.entities import TrainingRecommendationContext
from src.domain.training.services import TrainingRecommendationService


class GetTodayTrainingContextUseCase:
    def __init__(self, service: TrainingRecommendationService) -> None:
        self.service = service

    async def execute(self, user_id: UUID) -> TrainingRecommendationContextDTO:
        return self._to_dto(
            await self.service.build_context(user_id, date_type.today())
        )

    def _to_dto(
        self, context: TrainingRecommendationContext
    ) -> TrainingRecommendationContextDTO:
        return TrainingRecommendationContextDTO(
            recent_load=TrainingLoadSummaryDTO(**asdict(context.recent_load)),
            muscle_fatigue=[
                MuscleFatigueItemDTO(**asdict(item)) for item in context.muscle_fatigue
            ],
            exercise_trends=[
                ExercisePerformanceTrendDTO(**asdict(item))
                for item in context.exercise_trends
            ],
            suggested_focus=context.suggested_focus,
            avoid_focus=context.avoid_focus,
            reason=context.reason,
        )
