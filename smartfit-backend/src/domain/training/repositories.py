from abc import ABC, abstractmethod
from datetime import date as date_type
from uuid import UUID

from src.domain.training.entities import (
    CompletedWorkout,
    SetLogWithExercise,
    WorkoutHealthMetrics,
)


class TrainingRepository(ABC):
    @abstractmethod
    async def get_completed_workouts(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[CompletedWorkout]:
        raise NotImplementedError

    @abstractmethod
    async def get_set_logs_with_exercise(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[SetLogWithExercise]:
        raise NotImplementedError

    @abstractmethod
    async def get_workout_health_metrics(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[WorkoutHealthMetrics]:
        raise NotImplementedError

    @abstractmethod
    async def get_exercise_history(
        self, user_id: UUID, exercise_id: UUID, limit: int
    ) -> list[SetLogWithExercise]:
        raise NotImplementedError
