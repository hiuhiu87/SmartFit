from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.ai.entities import AIRequest, AIWorkoutGenerationContext, AIWorkoutGenerationResult


class AIRequestRepository(ABC):
    @abstractmethod
    async def save(self, request: AIRequest) -> AIRequest:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 50) -> list[AIRequest]:
        raise NotImplementedError


class AIWorkoutGeneratorPort(ABC):
    @abstractmethod
    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        raise NotImplementedError
