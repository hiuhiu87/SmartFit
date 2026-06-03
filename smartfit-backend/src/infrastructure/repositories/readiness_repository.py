from datetime import datetime, timezone
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.readiness.entities import ReadinessScore
from src.domain.readiness.repositories import ReadinessRepository
from src.infrastructure.database.mapper import (
    readiness_score_model_to_domain,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel


class SQLModelReadinessRepository(ReadinessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, readiness_score: ReadinessScore) -> ReadinessScore:
        statement = select(ReadinessScoreModel).where(
            ReadinessScoreModel.user_id == readiness_score.user_id,
            ReadinessScoreModel.date == readiness_score.date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            model = ReadinessScoreModel(
                id=readiness_score.id or uuid4(),
                user_id=readiness_score.user_id,
                date=readiness_score.date,
            )
            self.session.add(model)

        model.score = readiness_score.score
        model.category = readiness_score.category.value
        model.recommendation = readiness_score.recommendation.value
        model.confidence = readiness_score.confidence
        model.explanation = readiness_score.explanation
        model.created_at = (
            readiness_score.created_at or model.created_at or datetime.now(timezone.utc)
        )
        model.updated_at = readiness_score.updated_at or datetime.now(timezone.utc)
        await self.session.flush()
        return readiness_score_model_to_domain(model)

    async def get_by_date(
        self, user_id: UUID, target_date: date
    ) -> ReadinessScore | None:
        statement = select(ReadinessScoreModel).where(
            ReadinessScoreModel.user_id == user_id,
            ReadinessScoreModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return readiness_score_model_to_domain(model) if model else None

    async def list_history(
        self, user_id: UUID, limit: int = 30
    ) -> list[ReadinessScore]:
        statement = (
            select(ReadinessScoreModel)
            .where(ReadinessScoreModel.user_id == user_id)
            .order_by(
                ReadinessScoreModel.date.desc(), ReadinessScoreModel.updated_at.desc()
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [
            readiness_score_model_to_domain(model) for model in result.scalars().all()
        ]

    async def get_latest(self, user_id: UUID) -> ReadinessScore | None:
        statement = (
            select(ReadinessScoreModel)
            .where(ReadinessScoreModel.user_id == user_id)
            .order_by(
                ReadinessScoreModel.date.desc(), ReadinessScoreModel.updated_at.desc()
            )
            .limit(1)
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return readiness_score_model_to_domain(model) if model else None
