from abc import ABC, abstractmethod

from src.domain.ai.ports import AIRequestRepository
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.health.repositories import HealthRepository
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.subscription.repositories import SubscriptionRepository
from src.domain.user.repositories import UserRepository
from src.domain.workout.repositories import WorkoutRepository


class UnitOfWork(ABC):
    users: UserRepository
    health: HealthRepository
    readiness: ReadinessRepository
    exercises: ExerciseRepository
    workouts: WorkoutRepository
    ai_requests: AIRequestRepository
    subscriptions: SubscriptionRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
