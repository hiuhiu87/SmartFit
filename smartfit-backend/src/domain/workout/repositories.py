from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.workout.entities import WorkoutLog, WorkoutPlan, WorkoutSetLog


class WorkoutRepository(ABC):
    @abstractmethod
    async def save_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        raise NotImplementedError

    @abstractmethod
    async def get_plan_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def save_log(self, log: WorkoutLog) -> WorkoutLog:
        raise NotImplementedError

    @abstractmethod
    async def save_set_log(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        raise NotImplementedError

    @abstractmethod
    async def list_workout_history(self, user_id: UUID, limit: int = 30) -> list[WorkoutLog]:
        raise NotImplementedError
