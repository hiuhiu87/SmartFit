from abc import ABC, abstractmethod
from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from src.domain.workout.entities import (
    WorkoutFeedback,
    WorkoutHistoryItem,
    WorkoutLog,
    WorkoutPlan,
    WorkoutSetLog,
)


class WorkoutRepository(ABC):
    @abstractmethod
    async def save_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        raise NotImplementedError

    @abstractmethod
    async def get_plan_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def get_plan_detail_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def update_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        raise NotImplementedError

    @abstractmethod
    async def update_plan_exercise(
        self, plan_exercise: WorkoutPlanExercise
    ) -> WorkoutPlanExercise:
        raise NotImplementedError

    @abstractmethod
    async def create_workout_log(
        self, user_id: UUID, workout_plan_id: UUID, started_at: datetime
    ) -> WorkoutLog:
        raise NotImplementedError

    @abstractmethod
    async def get_workout_log_by_id(self, workout_log_id: UUID) -> WorkoutLog | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_log_by_plan_id(
        self, user_id: UUID, workout_plan_id: UUID
    ) -> WorkoutLog | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_log_by_plan_id(
        self, user_id: UUID, workout_plan_id: UUID
    ) -> WorkoutLog | None:
        raise NotImplementedError

    @abstractmethod
    async def log_set(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        raise NotImplementedError

    @abstractmethod
    async def upsert_set_log(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        raise NotImplementedError

    @abstractmethod
    async def get_set_logs_by_workout_log_id(
        self, workout_log_id: UUID
    ) -> list[WorkoutSetLog]:
        raise NotImplementedError

    @abstractmethod
    async def complete_workout_log(self, workout_log: WorkoutLog) -> WorkoutLog:
        raise NotImplementedError

    @abstractmethod
    async def create_or_update_feedback(
        self, feedback: WorkoutFeedback
    ) -> WorkoutFeedback:
        raise NotImplementedError

    @abstractmethod
    async def get_history(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        status: str | None,
        from_date: date_type | None,
        to_date: date_type | None,
    ) -> tuple[list[WorkoutHistoryItem], int]:
        raise NotImplementedError
