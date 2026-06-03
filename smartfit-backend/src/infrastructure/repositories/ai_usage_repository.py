from datetime import date as date_type
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.ai.entities import AIRequestLog, AIUsageDaily
from src.domain.ai.repositories import AIUsageRepository
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.mapper import (
    ai_request_log_domain_to_model,
    ai_usage_daily_model_to_domain,
)
from src.infrastructure.database.models.ai_model import (
    AIRequestModel,
    AIUsageDailyModel,
)


class SQLModelAIUsageRepository(AIUsageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_daily_usage(
        self, user_id: UUID, target_date: date_type
    ) -> AIUsageDaily | None:
        statement = select(AIUsageDailyModel).where(
            AIUsageDailyModel.user_id == user_id,
            AIUsageDailyModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return ai_usage_daily_model_to_domain(model) if model else None

    async def increment_usage(
        self, user_id: UUID, target_date: date_type, request_type: str
    ) -> AIUsageDaily:
        # TODO: add row-level locking if AI traffic becomes high.
        statement = select(AIUsageDailyModel).where(
            AIUsageDailyModel.user_id == user_id,
            AIUsageDailyModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if model is None:
            model = AIUsageDailyModel(
                user_id=user_id, date=target_date, created_at=now, updated_at=now
            )
            self.session.add(model)

        if request_type == "generate_workout":
            model.ai_workout_count += 1
        elif request_type == "chat":
            model.ai_chat_count += 1
        elif request_type == "replace_exercise":
            model.ai_replacement_count += 1
        elif request_type == "weekly_report":
            model.ai_weekly_report_count += 1
        model.total_ai_count += 1
        model.updated_at = now
        await self.session.flush()
        return ai_usage_daily_model_to_domain(model)

    async def save_request_log(self, log: AIRequestLog) -> AIRequestLog:
        model = None
        if log.id is not None:
            result = await self.session.execute(
                select(AIRequestModel).where(AIRequestModel.id == log.id)
            )
            model = result.scalar_one_or_none()
        if model is None:
            model = ai_request_log_domain_to_model(log)
            if model.id is None:
                model.id = uuid4()
            self.session.add(model)
        else:
            if model.created_at is None:
                model.created_at = log.created_at or utcnow()
            model.user_id = log.user_id
            model.workout_plan_id = log.workout_plan_id
            model.request_type = log.request_type
            model.provider = log.provider
            model.model_name = log.model_name
            model.generation_mode = log.generation_mode
            # Keep compatibility with databases where these legacy columns are NOT NULL.
            model.prompt = log.prompt or ""
            model.response = log.response or ""
            model.input_payload = log.input_payload or {}
            model.output_payload = log.output_payload or {}
            model.status = log.status
            model.error_code = log.error_code
            model.error_message = log.error_message
            model.fallback_used = log.fallback_used
            model.latency_ms = log.latency_ms
            model.request_metadata = log.metadata or {}
            model.updated_at = utcnow()
        await self.session.flush()
        log.id = model.id
        log.created_at = model.created_at
        return AIRequestLog(
            id=model.id,
            user_id=model.user_id,
            workout_plan_id=model.workout_plan_id,
            request_type=model.request_type,
            provider=model.provider,
            model_name=model.model_name,
            generation_mode=model.generation_mode,
            prompt=model.prompt,
            response=model.response,
            input_payload=dict(model.input_payload or {}),
            output_payload=dict(model.output_payload or {}),
            status=model.status,
            error_code=model.error_code,
            error_message=model.error_message,
            fallback_used=model.fallback_used,
            latency_ms=model.latency_ms,
            metadata=dict(model.request_metadata or {}),
            created_at=model.created_at,
        )
