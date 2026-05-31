from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.exercise.entities import Exercise


class ExerciseRepository(ABC):
    @abstractmethod
    async def list_exercises(self, limit: int = 100, offset: int = 0) -> list[Exercise]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Exercise | None:
        raise NotImplementedError

    @abstractmethod
    async def get_alternative(self, exercise_id: UUID) -> Exercise | None:
        raise NotImplementedError
