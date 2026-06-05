from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.progression.entities import ExercisePerformanceHistory


class ProgressionRepository(ABC):
    @abstractmethod
    async def get_exercise_performance_history(
        self, user_id: UUID, exercise_id: UUID, limit: int
    ) -> ExercisePerformanceHistory:
        raise NotImplementedError

    @abstractmethod
    async def get_recent_performance_for_exercises(
        self,
        user_id: UUID,
        exercise_ids: list[UUID],
        limit_per_exercise: int,
    ) -> dict[UUID, ExercisePerformanceHistory]:
        raise NotImplementedError
