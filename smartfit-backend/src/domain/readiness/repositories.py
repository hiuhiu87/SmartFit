from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.readiness.entities import ReadinessScore


class ReadinessRepository(ABC):
    @abstractmethod
    async def save(self, readiness_score: ReadinessScore) -> ReadinessScore:
        raise NotImplementedError

    @abstractmethod
    async def get_by_date(
        self, user_id: UUID, target_date: date
    ) -> ReadinessScore | None:
        raise NotImplementedError

    @abstractmethod
    async def list_history(
        self, user_id: UUID, limit: int = 30
    ) -> list[ReadinessScore]:
        raise NotImplementedError
