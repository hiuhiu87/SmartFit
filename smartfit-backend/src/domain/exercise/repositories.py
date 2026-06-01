from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.exercise.entities import Exercise


class ExerciseRepository(ABC):
    @abstractmethod
    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_filters(
        self,
        primary_muscle: str | None,
        equipment: str | None,
        difficulty: str | None,
        movement_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Exercise], int]:
        raise NotImplementedError

    @abstractmethod
    async def find_allowed(
        self,
        equipment: list[str],
        focus_muscle: str | None,
        level: str | None,
        limit: int = 20,
    ) -> list[Exercise]:
        raise NotImplementedError

    @abstractmethod
    async def list_exercises(self, limit: int = 100, offset: int = 0) -> list[Exercise]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Exercise | None:
        raise NotImplementedError

    @abstractmethod
    async def get_alternative(self, exercise_id: UUID) -> Exercise | None:
        raise NotImplementedError

    @abstractmethod
    async def find_replacement_candidates(
        self,
        current_exercise_id: UUID,
        primary_muscle: str,
        equipment: list[str],
        level: str | None,
        limit: int = 5,
    ) -> list[Exercise]:
        raise NotImplementedError
