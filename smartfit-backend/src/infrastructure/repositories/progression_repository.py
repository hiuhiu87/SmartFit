from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.progression.entities import (
    ExercisePerformanceHistory,
    ExerciseSessionPerformance,
    SetPerformance,
)
from src.domain.progression.repositories import ProgressionRepository
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.workout_model import (
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutSetLogModel,
)


class SQLModelProgressionRepository(ProgressionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_exercise_performance_history(
        self, user_id: UUID, exercise_id: UUID, limit: int
    ) -> ExercisePerformanceHistory:
        histories = await self.get_recent_performance_for_exercises(
            user_id=user_id,
            exercise_ids=[exercise_id],
            limit_per_exercise=limit,
        )
        return histories.get(
            exercise_id,
            ExercisePerformanceHistory(
                exercise_id=exercise_id,
                exercise_name="",
            ),
        )

    async def get_recent_performance_for_exercises(
        self,
        user_id: UUID,
        exercise_ids: list[UUID],
        limit_per_exercise: int,
    ) -> dict[UUID, ExercisePerformanceHistory]:
        if not exercise_ids:
            return {}

        statement = (
            select(
                ExerciseModel,
                WorkoutLogModel,
                WorkoutSetLogModel,
            )
            .select_from(WorkoutSetLogModel)
            .join(
                WorkoutLogModel,
                WorkoutLogModel.id == WorkoutSetLogModel.workout_log_id,
            )
            .join(
                WorkoutPlanExerciseModel,
                WorkoutPlanExerciseModel.id
                == WorkoutSetLogModel.workout_plan_exercise_id,
            )
            .join(
                ExerciseModel,
                ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id,
            )
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.completed_at.is_not(None),
                WorkoutPlanExerciseModel.exercise_id.in_(exercise_ids),
            )
            .order_by(
                ExerciseModel.id.asc(),
                WorkoutLogModel.completed_at.desc(),
                WorkoutSetLogModel.set_number.asc(),
            )
        )
        result = await self.session.execute(statement)

        histories: dict[UUID, ExercisePerformanceHistory] = {}
        sessions: dict[UUID, dict[UUID, ExerciseSessionPerformance]] = defaultdict(dict)
        for exercise, workout_log, set_log in result.all():
            history = histories.setdefault(
                exercise.id,
                ExercisePerformanceHistory(
                    exercise_id=exercise.id,
                    exercise_name=exercise.name,
                    equipment_type=exercise.equipment_type,
                    movement_type=exercise.movement_type,
                ),
            )
            exercise_sessions = sessions[exercise.id]
            if (
                workout_log.id not in exercise_sessions
                and len(exercise_sessions) >= limit_per_exercise
            ):
                continue
            session = exercise_sessions.setdefault(
                workout_log.id,
                ExerciseSessionPerformance(
                    workout_log_id=workout_log.id,
                    completed_at=workout_log.completed_at,
                ),
            )
            session.sets.append(
                SetPerformance(
                    weight=set_log.weight_kg,
                    reps=set_log.reps_completed,
                    rpe=set_log.rpe,
                    completed=set_log.completed,
                )
            )
            history.recent_sessions = list(exercise_sessions.values())

        for exercise_id in exercise_ids:
            histories.setdefault(
                exercise_id,
                ExercisePerformanceHistory(
                    exercise_id=exercise_id,
                    exercise_name="",
                ),
            )
        return histories
