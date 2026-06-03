import json
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.ai.entities import AIChatHistoryItem, AIChatMessage, AIRequest
from src.domain.ai.ports import AIRequestRepository
from src.domain.common.enums import AIRequestStatus, AIRequestType
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.models.ai_model import (
    AIChatMessageModel,
    AIRequestModel,
)


class SQLModelAIRequestRepository(AIRequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, request: AIRequest) -> AIRequest:
        statement = select(AIRequestModel).where(AIRequestModel.id == request.id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            model = AIRequestModel(
                id=request.id,
                user_id=request.user_id,
                workout_plan_id=request.workout_plan_id,
                request_type=request.request_type.value,
                provider=request.provider,
                model_name=request.model_name,
                generation_mode=request.generation_mode,
                status=request.status.value,
                prompt=request.prompt,
                response=request.response,
                input_payload=request.input_payload,
                output_payload=request.output_payload,
                error_code=request.error_code,
                error_message=request.error_message,
                fallback_used=request.fallback_used,
                latency_ms=request.latency_ms,
                request_metadata=request.metadata,
                created_at=request.created_at or utcnow(),
                updated_at=request.updated_at or utcnow(),
            )
            self.session.add(model)
        else:
            model.user_id = request.user_id
            model.workout_plan_id = request.workout_plan_id
            model.request_type = request.request_type.value
            model.provider = request.provider
            model.model_name = request.model_name
            model.generation_mode = request.generation_mode
            model.status = request.status.value
            model.prompt = request.prompt
            model.response = request.response
            model.input_payload = request.input_payload
            model.output_payload = request.output_payload
            model.error_code = request.error_code
            model.error_message = request.error_message
            model.fallback_used = request.fallback_used
            model.latency_ms = request.latency_ms
            model.request_metadata = request.metadata
            model.updated_at = request.updated_at or utcnow()
        await self.session.flush()
        return self._to_request(model)

    async def list_by_user(self, user_id: UUID, limit: int = 50) -> list[AIRequest]:
        statement = (
            select(AIRequestModel)
            .where(AIRequestModel.user_id == user_id)
            .order_by(AIRequestModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [self._to_request(model) for model in result.scalars().all()]

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
        if ai_request_id is None:
            request = AIRequest(
                id=uuid4(),
                user_id=user_id,
                workout_plan_id=workout_plan_id,
                request_type=AIRequestType.CHAT,
                provider="gemini",
                model_name="",
                generation_mode=None,
                status=AIRequestStatus.SUCCESS,
                prompt=message[:4000],
                response=None,
                input_payload={"message": message[:1000]},
                output_payload={},
                error_code=None,
                error_message=None,
                fallback_used=False,
                latency_ms=None,
                metadata={
                    "workout_id": str(workout_plan_id),
                    "workout_plan_exercise_id": (
                        str(workout_plan_exercise_id)
                        if workout_plan_exercise_id
                        else None
                    ),
                    "suggested_action": suggested_action,
                },
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            saved_request = await self.save(request)
            ai_request_id = saved_request.id
        else:
            request_statement = select(AIRequestModel).where(
                AIRequestModel.id == ai_request_id
            )
            request_result = await self.session.execute(request_statement)
            request_model = request_result.scalar_one_or_none()
            if request_model is not None:
                metadata = dict(request_model.request_metadata or {})
                metadata["workout_id"] = str(workout_plan_id)
                metadata["workout_plan_exercise_id"] = (
                    str(workout_plan_exercise_id) if workout_plan_exercise_id else None
                )
                if suggested_action is not None:
                    metadata["suggested_action"] = suggested_action
                request_model.request_metadata = metadata
                request_model.workout_plan_id = workout_plan_id
                request_model.updated_at = utcnow()

        content = message
        if role == "assistant" and suggested_action is not None:
            content = f"{message}\n\n[SUGGESTED_ACTION]{json.dumps(suggested_action)}"

        model = AIChatMessageModel(
            ai_request_id=ai_request_id,
            role=role,
            content=content[:4000],
            created_at=utcnow(),
        )
        self.session.add(model)
        await self.session.flush()
        return AIChatMessage(
            id=model.id,
            ai_request_id=model.ai_request_id,
            role=model.role,
            content=model.content,
            created_at=model.created_at,
        )

    async def list_chat_messages_by_workout(
        self,
        user_id: UUID,
        workout_plan_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AIChatHistoryItem], int]:
        statement = (
            select(AIChatMessageModel, AIRequestModel)
            .join(AIRequestModel, AIRequestModel.id == AIChatMessageModel.ai_request_id)
            .where(
                AIRequestModel.user_id == user_id,
                AIRequestModel.request_type == AIRequestType.CHAT.value,
                AIRequestModel.workout_plan_id == workout_plan_id,
            )
            .order_by(AIChatMessageModel.created_at.asc(), AIChatMessageModel.id.asc())
        )
        result = await self.session.execute(statement)
        filtered: list[AIChatHistoryItem] = []
        for message_model, request_model in result.all():
            metadata = dict(request_model.request_metadata or {})
            message, suggested_action = self._split_content(message_model.content)
            filtered.append(
                AIChatHistoryItem(
                    id=message_model.id,
                    ai_request_id=message_model.ai_request_id,
                    role=message_model.role,
                    message=message,
                    suggested_action=suggested_action,
                    workout_plan_exercise_id=(
                        UUID(metadata["workout_plan_exercise_id"])
                        if metadata.get("workout_plan_exercise_id")
                        else None
                    ),
                    created_at=message_model.created_at,
                )
            )
        total = len(filtered)
        return filtered[offset : offset + limit], total

    def _to_request(self, model: AIRequestModel) -> AIRequest:
        return AIRequest(
            id=model.id,
            user_id=model.user_id,
            workout_plan_id=model.workout_plan_id,
            request_type=AIRequestType(model.request_type),
            provider=model.provider,
            model_name=model.model_name,
            generation_mode=model.generation_mode,
            status=AIRequestStatus(model.status),
            prompt=model.prompt,
            response=model.response,
            input_payload=dict(model.input_payload or {}),
            output_payload=dict(model.output_payload or {}),
            error_code=model.error_code,
            error_message=model.error_message,
            fallback_used=model.fallback_used,
            latency_ms=model.latency_ms,
            metadata=dict(model.request_metadata or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _split_content(self, content: str) -> tuple[str, dict | None]:
        marker = "\n\n[SUGGESTED_ACTION]"
        if marker not in content:
            return content, None
        message, raw_action = content.split(marker, 1)
        try:
            return message, json.loads(raw_action)
        except json.JSONDecodeError:
            return message, None
