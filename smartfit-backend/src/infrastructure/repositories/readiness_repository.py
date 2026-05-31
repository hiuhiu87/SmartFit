from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.readiness.entities import ReadinessScore
from src.domain.readiness.repositories import ReadinessRepository
from src.infrastructure.database.mapper import readiness_score_domain_to_model, readiness_score_model_to_domain
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel


class SQLModelReadinessRepository(ReadinessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, readiness_score: ReadinessScore) -> ReadinessScore:
        model = readiness_score_domain_to_model(readiness_score)
        self.session.add(model)
        return readiness_score

    async def get_by_date(self, user_id: UUID, target_date: date) -> ReadinessScore | None:
        statement = select(ReadinessScoreModel).where(
            ReadinessScoreModel.user_id == user_id,
            ReadinessScoreModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return readiness_score_model_to_domain(model) if model else None

    async def list_history(self, user_id: UUID, limit: int = 30) -> list[ReadinessScore]:
        statement = select(ReadinessScoreModel).where(ReadinessScoreModel.user_id == user_id).limit(limit)
        result = await self.session.execute(statement)
        return [readiness_score_model_to_domain(model) for model in result.scalars().all()]
