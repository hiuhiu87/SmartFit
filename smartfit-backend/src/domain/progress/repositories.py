from abc import ABC, abstractmethod
from datetime import date as date_type
from uuid import UUID

from src.domain.progress.entities import MuscleDistributionItem, PersonalRecord
from src.domain.workout.entities import WorkoutLog


class ProgressRepository(ABC):
    @abstractmethod
    async def get_completed_workout_logs(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[WorkoutLog]:
        raise NotImplementedError

    @abstractmethod
    async def get_total_volume(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> float:
        raise NotImplementedError

    @abstractmethod
    async def get_average_readiness(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> float | None:
        raise NotImplementedError

    @abstractmethod
    async def get_muscle_distribution(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[MuscleDistributionItem]:
        raise NotImplementedError

    @abstractmethod
    async def get_personal_records(
        self,
        user_id: UUID,
        limit: int,
        exercise_id: UUID | None,
        metric: str | None,
    ) -> list[PersonalRecord]:
        raise NotImplementedError
