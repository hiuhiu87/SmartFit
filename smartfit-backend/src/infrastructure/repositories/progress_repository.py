from collections import defaultdict
from datetime import date as date_type
from uuid import UUID

from sqlalchemy import distinct, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.progress.entities import MuscleDistributionItem, PersonalRecord
from src.domain.progress.repositories import ProgressRepository
from src.domain.workout.entities import WorkoutLog
from src.infrastructure.database.mapper import workout_log_model_to_domain
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.workout_model import (
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)


class SQLModelProgressRepository(ProgressRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_completed_workout_logs(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[WorkoutLog]:
        completed_date = func.date(WorkoutLogModel.completed_at)
        statement = (
            select(WorkoutLogModel, WorkoutPlanModel.title, WorkoutPlanModel.focus)
            .join(WorkoutPlanModel, WorkoutPlanModel.id == WorkoutLogModel.workout_plan_id)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                completed_date >= from_date,
                completed_date <= to_date,
            )
            .order_by(WorkoutLogModel.completed_at.desc())
        )
        result = await self.session.execute(statement)
        logs: list[WorkoutLog] = []
        for model, title, focus in result.all():
            log = workout_log_model_to_domain(model)
            log.title = title
            log.focus_muscle = focus
            logs.append(log)
        return logs

    async def get_total_volume(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> float:
        completed_date = func.date(WorkoutLogModel.completed_at)
        statement = (
            select(func.coalesce(func.sum(WorkoutLogModel.total_volume), 0.0))
            .select_from(WorkoutLogModel)
            .join(WorkoutPlanModel, WorkoutPlanModel.id == WorkoutLogModel.workout_plan_id)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                completed_date >= from_date,
                completed_date <= to_date,
            )
        )
        result = await self.session.execute(statement)
        return float(result.scalar_one() or 0.0)

    async def get_average_readiness(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> float | None:
        statement = select(func.avg(ReadinessScoreModel.score)).where(
            ReadinessScoreModel.user_id == user_id,
            ReadinessScoreModel.date >= from_date,
            ReadinessScoreModel.date <= to_date,
        )
        result = await self.session.execute(statement)
        value = result.scalar_one()
        return float(value) if value is not None else None

    async def get_muscle_distribution(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[MuscleDistributionItem]:
        completed_date = func.date(WorkoutLogModel.completed_at)
        volume_expr = func.coalesce(WorkoutSetLogModel.weight_kg, 0) * func.coalesce(
            WorkoutSetLogModel.reps_completed, 0
        )
        statement = (
            select(
                ExerciseModel.muscle_group,
                func.count(distinct(WorkoutLogModel.id)),
                func.count(WorkoutSetLogModel.id),
                func.coalesce(func.sum(volume_expr), 0.0),
            )
            .select_from(WorkoutLogModel)
            .join(WorkoutPlanModel, WorkoutPlanModel.id == WorkoutLogModel.workout_plan_id)
            .join(
                WorkoutSetLogModel,
                WorkoutSetLogModel.workout_log_id == WorkoutLogModel.id,
            )
            .join(
                WorkoutPlanExerciseModel,
                WorkoutPlanExerciseModel.id == WorkoutSetLogModel.workout_plan_exercise_id,
            )
            .join(ExerciseModel, ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                WorkoutSetLogModel.completed.is_(True),
                completed_date >= from_date,
                completed_date <= to_date,
            )
            .group_by(ExerciseModel.muscle_group)
            .order_by(func.coalesce(func.sum(volume_expr), 0.0).desc())
        )
        result = await self.session.execute(statement)
        return [
            MuscleDistributionItem(
                muscle=muscle,
                workout_count=int(workout_count),
                set_count=int(set_count),
                volume=float(volume),
            )
            for muscle, workout_count, set_count, volume in result.all()
        ]

    async def get_personal_records(
        self,
        user_id: UUID,
        limit: int,
        exercise_id: UUID | None,
        metric: str | None,
    ) -> list[PersonalRecord]:
        statement = (
            select(
                ExerciseModel.id,
                ExerciseModel.name,
                ExerciseModel.muscle_group,
                WorkoutLogModel.workout_plan_id,
                WorkoutLogModel.id,
                WorkoutLogModel.completed_at,
                WorkoutSetLogModel.weight_kg,
                WorkoutSetLogModel.reps_completed,
            )
            .select_from(WorkoutSetLogModel)
            .join(WorkoutLogModel, WorkoutLogModel.id == WorkoutSetLogModel.workout_log_id)
            .join(
                WorkoutPlanExerciseModel,
                WorkoutPlanExerciseModel.id == WorkoutSetLogModel.workout_plan_exercise_id,
            )
            .join(ExerciseModel, ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                WorkoutSetLogModel.completed.is_(True),
                WorkoutSetLogModel.weight_kg.is_not(None),
                WorkoutSetLogModel.reps_completed.is_not(None),
            )
            .order_by(WorkoutLogModel.completed_at.desc())
        )
        if exercise_id is not None:
            statement = statement.where(ExerciseModel.id == exercise_id)

        result = await self.session.execute(statement)
        rows = result.all()

        grouped: dict[UUID, list[tuple]] = defaultdict(list)
        for row in rows:
            grouped[row[0]].append(row)

        records: list[PersonalRecord] = []
        for grouped_exercise_id, exercise_rows in grouped.items():
            first = exercise_rows[0]
            best_weight = max(float(row[6]) for row in exercise_rows)
            best_reps = max(int(row[7]) for row in exercise_rows)
            best_set_volume = max(float(row[6]) * int(row[7]) for row in exercise_rows)
            best_estimated_1rm = max(
                round(float(row[6]) * (1 + int(row[7]) / 30), 2) for row in exercise_rows
            )

            def score(row: tuple) -> float:
                weight = float(row[6])
                reps = int(row[7])
                if metric == "max_weight":
                    return weight
                if metric == "max_reps":
                    return reps
                if metric == "max_volume":
                    return weight * reps
                return round(weight * (1 + reps / 30), 2)

            best_row = max(
                exercise_rows,
                key=lambda row: (score(row), row[5]),
            )
            records.append(
                PersonalRecord(
                    exercise_id=grouped_exercise_id,
                    exercise_name=first[1],
                    primary_muscle=first[2],
                    best_weight=best_weight,
                    best_reps=best_reps,
                    best_set_volume=best_set_volume,
                    estimated_1rm=best_estimated_1rm,
                    workout_id=best_row[3],
                    workout_log_id=best_row[4],
                    achieved_at=best_row[5],
                )
            )

        def sort_value(record: PersonalRecord) -> tuple:
            if metric == "max_weight":
                return (record.best_weight, record.achieved_at)
            if metric == "max_reps":
                return (record.best_reps, record.achieved_at)
            if metric == "max_volume":
                return (record.best_set_volume, record.achieved_at)
            return (record.estimated_1rm, record.achieved_at)

        records.sort(key=sort_value, reverse=True)
        return records[:limit]
