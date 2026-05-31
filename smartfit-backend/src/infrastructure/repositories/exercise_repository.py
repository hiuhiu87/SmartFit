from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.exercise.entities import Exercise
from src.domain.exercise.repositories import ExerciseRepository
from src.infrastructure.database.mapper import exercise_model_to_domain
from src.infrastructure.database.models.exercise_model import (
    ExerciseAlternativeModel,
    ExerciseModel,
)


class SQLModelExerciseRepository(ExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_exercises(self, limit: int = 100, offset: int = 0) -> list[Exercise]:
        statement = select(ExerciseModel).offset(offset).limit(limit)
        result = await self.session.execute(statement)
        return [exercise_model_to_domain(model) for model in result.scalars().all()]

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        statement = select(ExerciseModel).where(ExerciseModel.id == exercise_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return exercise_model_to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> Exercise | None:
        statement = select(ExerciseModel).where(ExerciseModel.slug == slug)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return exercise_model_to_domain(model) if model else None

    async def get_alternative(self, exercise_id: UUID) -> Exercise | None:
        statement = select(ExerciseAlternativeModel).where(
            ExerciseAlternativeModel.exercise_id == exercise_id
        )
        result = await self.session.execute(statement)
        alternative = result.scalar_one_or_none()
        if alternative is None:
            return None
        return await self.get_by_id(alternative.alternative_exercise_id)
