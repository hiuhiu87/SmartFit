from dataclasses import asdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.workout.entities import WorkoutLog, WorkoutPlan, WorkoutSetLog
from src.domain.workout.repositories import WorkoutRepository
from src.infrastructure.database.mapper import workout_plan_domain_to_model, workout_plan_model_to_domain
from src.infrastructure.database.models.workout_model import WorkoutLogModel, WorkoutPlanModel, WorkoutSetLogModel


class SQLModelWorkoutRepository(WorkoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        model = workout_plan_domain_to_model(plan)
        self.session.add(model)
        return plan

    async def get_plan_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        statement = select(WorkoutPlanModel).where(WorkoutPlanModel.id == workout_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return workout_plan_model_to_domain(model) if model else None

    async def save_log(self, log: WorkoutLog) -> WorkoutLog:
        model = WorkoutLogModel.model_validate(asdict(log))
        self.session.add(model)
        return log

    async def save_set_log(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        model = WorkoutSetLogModel.model_validate(asdict(set_log))
        self.session.add(model)
        return set_log

    async def list_workout_history(self, user_id: UUID, limit: int = 30) -> list[WorkoutLog]:
        statement = select(WorkoutLogModel).where(WorkoutLogModel.user_id == user_id).limit(limit)
        result = await self.session.execute(statement)
        models = result.scalars().all()
        return [
            WorkoutLog(
                id=model.id,
                workout_plan_id=model.workout_plan_id,
                user_id=model.user_id,
                started_at=model.started_at,
                completed_at=model.completed_at,
                duration_minutes=model.duration_minutes,
                notes=model.notes,
                sets=[],
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            for model in models
        ]
