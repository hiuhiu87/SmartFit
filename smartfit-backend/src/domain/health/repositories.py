from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.health.entities import HealthSummary, ManualCheckin


class HealthRepository(ABC):
    @abstractmethod
    async def save_summary(self, summary: HealthSummary) -> HealthSummary:
        raise NotImplementedError

    @abstractmethod
    async def save_manual_checkin(self, checkin: ManualCheckin) -> ManualCheckin:
        raise NotImplementedError

    @abstractmethod
    async def get_summary_by_date(
        self, user_id: UUID, target_date: date
    ) -> HealthSummary | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_summary(self, user_id: UUID) -> HealthSummary | None:
        raise NotImplementedError

    @abstractmethod
    async def get_recent_summaries(
        self, user_id: UUID, before_date: date, limit: int
    ) -> list[HealthSummary]:
        raise NotImplementedError

    @abstractmethod
    async def get_manual_checkin_by_date(
        self, user_id: UUID, target_date: date
    ) -> ManualCheckin | None:
        raise NotImplementedError
