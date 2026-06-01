from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.ai.entities import (
    AIChatHistoryItem,
    AIChatContext,
    AIChatMessage,
    AIChatResult,
    AIRequest,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)


class AIRequestRepository(ABC):
    @abstractmethod
    async def save(self, request: AIRequest) -> AIRequest:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: UUID, limit: int = 50) -> list[AIRequest]:
        raise NotImplementedError

    @abstractmethod
    async def save_chat_message(
        self,
        user_id: UUID,
        workout_plan_id: UUID,
        workout_plan_exercise_id: UUID | None,
        role: str,
        message: str,
        suggested_action: dict | None = None,
        ai_request_id: UUID | None = None,
    ) -> AIChatMessage:
        raise NotImplementedError

    @abstractmethod
    async def list_chat_messages_by_workout(
        self,
        user_id: UUID,
        workout_plan_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AIChatHistoryItem], int]:
        raise NotImplementedError


class AIWorkoutGeneratorPort(ABC):
    @abstractmethod
    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        raise NotImplementedError

    @abstractmethod
    async def chat(self, context: AIChatContext) -> AIChatResult:
        raise NotImplementedError
