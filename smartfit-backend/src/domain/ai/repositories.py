from abc import ABC, abstractmethod
from datetime import date as date_type
from uuid import UUID

from src.domain.ai.entities import AIRequestLog, AIUsageDaily


class AIUsageRepository(ABC):
    @abstractmethod
    async def get_daily_usage(
        self, user_id: UUID, target_date: date_type
    ) -> AIUsageDaily | None:
        raise NotImplementedError

    @abstractmethod
    async def increment_usage(
        self, user_id: UUID, target_date: date_type, request_type: str
    ) -> AIUsageDaily:
        raise NotImplementedError

    @abstractmethod
    async def save_request_log(self, log: AIRequestLog) -> AIRequestLog:
        raise NotImplementedError
