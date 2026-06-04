from datetime import date as date_type
from uuid import UUID

from sqlalchemy import Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.training.entities import (
    CompletedWorkout,
    SetLogWithExercise,
    WorkoutHealthMetrics,
)
from src.domain.training.repositories import TrainingRepository
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.workout_model import (
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)


class SQLModelTrainingRepository(TrainingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_completed_workouts(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[CompletedWorkout]:
        statement = (
            select(WorkoutLogModel, WorkoutPlanModel)
            .join(
                WorkoutPlanModel, WorkoutPlanModel.id == WorkoutLogModel.workout_plan_id
            )
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                cast(WorkoutLogModel.completed_at, Date) >= from_date,
                cast(WorkoutLogModel.completed_at, Date) <= to_date,
            )
            .order_by(WorkoutLogModel.completed_at.desc())
        )
        result = await self.session.execute(statement)
        return [
            CompletedWorkout(
                workout_log_id=log.id,
                workout_plan_id=plan.id,
                user_id=log.user_id,
                completed_at=log.completed_at,
                duration_minutes=log.duration_minutes,
                total_volume=log.total_volume,
                focus_muscle=plan.focus,
            )
            for log, plan in result.all()
            if log.completed_at is not None
        ]

    async def get_set_logs_with_exercise(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[SetLogWithExercise]:
        statement = (
            select(
                WorkoutSetLogModel,
                WorkoutLogModel,
                WorkoutPlanExerciseModel,
                ExerciseModel,
            )
            .join(
                WorkoutLogModel, WorkoutLogModel.id == WorkoutSetLogModel.workout_log_id
            )
            .join(
                WorkoutPlanExerciseModel,
                WorkoutPlanExerciseModel.id
                == WorkoutSetLogModel.workout_plan_exercise_id,
            )
            .join(
                ExerciseModel, ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id
            )
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                cast(WorkoutLogModel.completed_at, Date) >= from_date,
                cast(WorkoutLogModel.completed_at, Date) <= to_date,
            )
            .order_by(
                WorkoutLogModel.completed_at.asc(),
                WorkoutPlanExerciseModel.order_index.asc(),
                WorkoutSetLogModel.set_number.asc(),
            )
        )
        result = await self.session.execute(statement)
        return [
            self._set_log_with_exercise(set_log, log, plan_exercise, exercise)
            for set_log, log, plan_exercise, exercise in result.all()
        ]

    async def get_workout_health_metrics(
        self, user_id: UUID, from_date: date_type, to_date: date_type
    ) -> list[WorkoutHealthMetrics]:
        statement = (
            select(WorkoutLogModel)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                cast(WorkoutLogModel.completed_at, Date) >= from_date,
                cast(WorkoutLogModel.completed_at, Date) <= to_date,
            )
            .order_by(WorkoutLogModel.completed_at.desc())
        )
        result = await self.session.execute(statement)
        return [
            WorkoutHealthMetrics(
                workout_log_id=log.id,
                completed_at=log.completed_at,
                duration_minutes=log.duration_minutes,
                active_energy_burned=log.calories_burned,
                avg_heart_rate=log.avg_heart_rate,
            )
            for log in result.scalars().all()
        ]

    async def get_exercise_history(
        self, user_id: UUID, exercise_id: UUID, limit: int
    ) -> list[SetLogWithExercise]:
        statement = (
            select(
                WorkoutSetLogModel,
                WorkoutLogModel,
                WorkoutPlanExerciseModel,
                ExerciseModel,
            )
            .join(
                WorkoutLogModel, WorkoutLogModel.id == WorkoutSetLogModel.workout_log_id
            )
            .join(
                WorkoutPlanExerciseModel,
                WorkoutPlanExerciseModel.id
                == WorkoutSetLogModel.workout_plan_exercise_id,
            )
            .join(
                ExerciseModel, ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id
            )
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutPlanExerciseModel.exercise_id == exercise_id,
                WorkoutLogModel.completed_at.is_not(None),
            )
            .order_by(
                WorkoutLogModel.completed_at.desc(),
                WorkoutSetLogModel.set_number.desc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)
        rows = [
            self._set_log_with_exercise(set_log, log, plan_exercise, exercise)
            for set_log, log, plan_exercise, exercise in result.all()
        ]
        return list(reversed(rows))

    def _set_log_with_exercise(
        self,
        set_log: WorkoutSetLogModel,
        log: WorkoutLogModel,
        plan_exercise: WorkoutPlanExerciseModel,
        exercise: ExerciseModel,
    ) -> SetLogWithExercise:
        return SetLogWithExercise(
            workout_log_id=log.id,
            workout_plan_exercise_id=plan_exercise.id,
            exercise_id=exercise.id,
            exercise_name=exercise.name,
            primary_muscle=exercise.muscle_group,
            secondary_muscles=exercise.secondary_muscles or [],
            completed_at=log.completed_at,
            set_number=set_log.set_number,
            reps_completed=set_log.reps_completed,
            weight_kg=set_log.weight_kg,
            rpe=set_log.rpe,
            completed=set_log.completed,
        )
