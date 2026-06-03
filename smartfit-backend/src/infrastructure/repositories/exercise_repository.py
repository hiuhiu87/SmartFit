from uuid import UUID

from sqlalchemy import func
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
        items, _ = await self.find_by_filters(
            primary_muscle=None,
            equipment=None,
            difficulty=None,
            movement_type=None,
            limit=limit,
            offset=offset,
        )
        return items

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        statement = select(ExerciseModel).where(
            ExerciseModel.id == exercise_id, ExerciseModel.is_active.is_(True)
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return exercise_model_to_domain(model) if model else None

    async def find_by_filters(
        self,
        primary_muscle: str | None,
        equipment: str | None,
        difficulty: str | None,
        movement_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Exercise], int]:
        filters = [ExerciseModel.is_active.is_(True)]
        if primary_muscle is not None:
            filters.append(ExerciseModel.muscle_group == primary_muscle)
        if equipment is not None:
            filters.append(ExerciseModel.equipment_type == equipment)
        if difficulty is not None:
            filters.append(ExerciseModel.training_level == difficulty)
        if movement_type is not None:
            filters.append(ExerciseModel.movement_type == movement_type)

        count_statement = (
            select(func.count()).select_from(ExerciseModel).where(*filters)
        )
        count_result = await self.session.execute(count_statement)
        total = int(count_result.scalar_one())

        statement = (
            select(ExerciseModel)
            .where(*filters)
            .order_by(ExerciseModel.muscle_group.asc(), ExerciseModel.name.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        items = [exercise_model_to_domain(model) for model in result.scalars().all()]
        return items, total

    async def find_allowed(
        self,
        equipment: list[str],
        focus_muscle: str | None,
        level: str | None,
        limit: int = 100,
    ) -> list[Exercise]:
        allowed_equipment = list(
            dict.fromkeys(
                equipment + (["bodyweight"] if "bodyweight" not in equipment else [])
            )
        )
        base_filters = [
            ExerciseModel.is_active.is_(True),
            ExerciseModel.equipment_type.in_(allowed_equipment),
        ]
        if focus_muscle is not None:
            base_filters.append(ExerciseModel.muscle_group == focus_muscle)

        statement = select(ExerciseModel).where(*base_filters)
        if level is not None:
            allowed_levels = ["beginner", "intermediate"]
            if level == "intermediate":
                allowed_levels = ["beginner", "intermediate"]
            elif level == "advanced":
                allowed_levels = ["beginner", "intermediate", "advanced"]
            statement_with_level = (
                statement.where(ExerciseModel.training_level.in_(allowed_levels))
                .order_by(ExerciseModel.muscle_group.asc(), ExerciseModel.name.asc())
                .limit(limit)
            )
            level_result = await self.session.execute(statement_with_level)
            level_items = [
                exercise_model_to_domain(model)
                for model in level_result.scalars().all()
            ]
            if level_items:
                return level_items

        statement = statement.order_by(
            ExerciseModel.muscle_group.asc(), ExerciseModel.name.asc()
        ).limit(limit)
        result = await self.session.execute(statement)
        return [exercise_model_to_domain(model) for model in result.scalars().all()]

    async def get_by_slug(self, slug: str) -> Exercise | None:
        statement = select(ExerciseModel).where(
            ExerciseModel.slug == slug, ExerciseModel.is_active.is_(True)
        )
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

    async def find_replacement_candidates(
        self,
        current_exercise_id: UUID,
        primary_muscle: str,
        equipment: list[str],
        level: str | None,
        limit: int = 5,
    ) -> list[Exercise]:
        allowed_equipment = list(
            dict.fromkeys(
                equipment + (["bodyweight"] if "bodyweight" not in equipment else [])
            )
        )
        filters = [
            ExerciseModel.is_active.is_(True),
            ExerciseModel.id != current_exercise_id,
            ExerciseModel.muscle_group == primary_muscle,
            ExerciseModel.equipment_type.in_(allowed_equipment),
        ]
        statement = select(ExerciseModel).where(*filters)
        if level is not None:
            level_statement = (
                statement.where(ExerciseModel.training_level == level)
                .order_by(ExerciseModel.name.asc())
                .limit(limit)
            )
            level_result = await self.session.execute(level_statement)
            level_items = [
                exercise_model_to_domain(model)
                for model in level_result.scalars().all()
            ]
            if level_items:
                return level_items

        result = await self.session.execute(
            statement.order_by(ExerciseModel.name.asc()).limit(limit)
        )
        return [exercise_model_to_domain(model) for model in result.scalars().all()]
