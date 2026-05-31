from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.ai.entities import AIRequest


class AIRequestRepository(ABC):
    @abstractmethod
    async def save(self, request: AIRequest) -> AIRequest:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 50) -> list[AIRequest]:
        raise NotImplementedError


class AIClientPort(ABC):
    @abstractmethod
    async def send(self, prompt: str) -> str:
        raise NotImplementedError
