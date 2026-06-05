from datetime import date as date_type
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.common.enums import DifficultyFeedback
from src.domain.workout.entities import (
    WorkoutFeedback,
    WorkoutHistoryItem,
    WorkoutLog,
    WorkoutPlan,
    WorkoutSetLog,
)
from src.domain.workout.repositories import WorkoutRepository
from src.infrastructure.database.mapper import (
    workout_feedback_model_to_domain,
    workout_log_model_to_domain,
    workout_plan_exercise_domain_to_model,
    workout_plan_exercise_model_to_domain,
    workout_plan_domain_to_model,
    workout_plan_model_to_domain,
    workout_set_log_domain_to_model,
    workout_set_log_model_to_domain,
)
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.workout_model import (
    WorkoutFeedbackModel,
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)


class SQLModelWorkoutRepository(WorkoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        now = datetime.now(timezone.utc)
        if plan.created_at is None:
            plan.created_at = now
        plan.updated_at = now
        model = workout_plan_domain_to_model(plan)
        self.session.add(model)
        await self.session.flush()

        exercise_models: list[WorkoutPlanExerciseModel] = []
        for exercise in plan.exercises:
            exercise.workout_plan_id = model.id
            exercise_model = workout_plan_exercise_domain_to_model(exercise)
            self.session.add(exercise_model)
            exercise_models.append(exercise_model)
        await self.session.flush()

        saved_plan = workout_plan_model_to_domain(model)
        saved_plan.exercises = [
            workout_plan_exercise_model_to_domain(item)
            for item in sorted(exercise_models, key=lambda row: row.order_index)
        ]
        return saved_plan

    async def get_plan_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        statement = select(WorkoutPlanModel).where(WorkoutPlanModel.id == workout_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return workout_plan_model_to_domain(model)

    async def get_plan_detail_by_id(self, workout_id: UUID) -> WorkoutPlan | None:
        plan = await self.get_plan_by_id(workout_id)
        if plan is None:
            return None

        statement = (
            select(WorkoutPlanExerciseModel, ExerciseModel)
            .join(
                ExerciseModel, ExerciseModel.id == WorkoutPlanExerciseModel.exercise_id
            )
            .where(WorkoutPlanExerciseModel.workout_plan_id == workout_id)
            .order_by(WorkoutPlanExerciseModel.order_index.asc())
        )
        result = await self.session.execute(statement)
        exercises = []
        for plan_exercise_model, exercise_model in result.all():
            plan_exercise = workout_plan_exercise_model_to_domain(plan_exercise_model)
            plan_exercise.name = exercise_model.name
            plan_exercise.primary_muscle = exercise_model.muscle_group
            plan_exercise.equipment = exercise_model.equipment_type
            exercises.append(plan_exercise)
        plan.exercises = exercises
        return plan

    async def update_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        statement = select(WorkoutPlanModel).where(WorkoutPlanModel.id == plan.id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return await self.save_plan(plan)

        model.target_date = plan.target_date
        model.title = plan.title
        model.goal = plan.goal.value
        model.focus = plan.focus.value
        model.status = plan.status.value
        model.source = plan.source.value
        model.estimated_duration_minutes = plan.estimated_duration_minutes
        model.readiness_score = plan.readiness_score
        model.decision = plan.decision
        model.ai_reasoning_summary = plan.ai_reasoning_summary
        model.safety_note = plan.safety_note
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        saved = workout_plan_model_to_domain(model)
        saved.exercises = plan.exercises
        return saved

    async def update_plan_exercise(
        self, plan_exercise: WorkoutPlanExercise
    ) -> WorkoutPlanExercise:
        statement = select(WorkoutPlanExerciseModel).where(
            WorkoutPlanExerciseModel.id == plan_exercise.id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Workout plan exercise not found during update.")

        model.exercise_id = plan_exercise.exercise_id
        model.target_sets = plan_exercise.target_sets
        model.target_reps = plan_exercise.target_reps
        model.rest_seconds = plan_exercise.rest_seconds
        model.target_rpe = plan_exercise.target_rpe
        model.target_weight = plan_exercise.target_weight
        model.notes = plan_exercise.notes
        await self.session.flush()
        return workout_plan_exercise_model_to_domain(model)

    async def create_workout_log(
        self, user_id: UUID, workout_plan_id: UUID, started_at: datetime
    ) -> WorkoutLog:
        now = datetime.now(timezone.utc)
        model = WorkoutLogModel(
            user_id=user_id,
            workout_plan_id=workout_plan_id,
            started_at=started_at,
            created_at=now,
            updated_at=now,
            total_volume=0,
        )
        self.session.add(model)
        await self.session.flush()
        return workout_log_model_to_domain(model)

    async def get_workout_log_by_id(self, workout_log_id: UUID) -> WorkoutLog | None:
        statement = select(WorkoutLogModel).where(WorkoutLogModel.id == workout_log_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return workout_log_model_to_domain(model) if model else None

    async def get_active_log_by_plan_id(
        self, user_id: UUID, workout_plan_id: UUID
    ) -> WorkoutLog | None:
        statement = (
            select(WorkoutLogModel)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.workout_plan_id == workout_plan_id,
                WorkoutLogModel.completed_at.is_(None),
            )
            .order_by(WorkoutLogModel.created_at.desc())
        )
        result = await self.session.execute(statement)
        model = result.scalars().first()
        return workout_log_model_to_domain(model) if model else None

    async def get_latest_log_by_plan_id(
        self, user_id: UUID, workout_plan_id: UUID
    ) -> WorkoutLog | None:
        statement = (
            select(WorkoutLogModel)
            .where(
                WorkoutLogModel.user_id == user_id,
                WorkoutLogModel.workout_plan_id == workout_plan_id,
            )
            .order_by(
                WorkoutLogModel.completed_at.desc().nullslast(),
                WorkoutLogModel.created_at.desc(),
            )
        )
        result = await self.session.execute(statement)
        model = result.scalars().first()
        return workout_log_model_to_domain(model) if model else None

    async def log_set(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        model = workout_set_log_domain_to_model(set_log)
        self.session.add(model)
        await self.session.flush()
        return workout_set_log_model_to_domain(model)

    async def upsert_set_log(self, set_log: WorkoutSetLog) -> WorkoutSetLog:
        statement = select(WorkoutSetLogModel).where(
            WorkoutSetLogModel.workout_log_id == set_log.workout_log_id,
            WorkoutSetLogModel.workout_plan_exercise_id
            == set_log.workout_plan_exercise_id,
            WorkoutSetLogModel.set_number == set_log.set_number,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if model is None:
            model = workout_set_log_domain_to_model(set_log)
            if model.created_at is None:
                model.created_at = now
            model.updated_at = now
            self.session.add(model)
        else:
            model.reps_completed = set_log.reps_completed
            model.weight_kg = set_log.weight_kg
            model.rpe = set_log.rpe
            model.completed = set_log.completed
            model.updated_at = now
        await self.session.flush()
        return workout_set_log_model_to_domain(model)

    async def get_set_logs_by_workout_log_id(
        self, workout_log_id: UUID
    ) -> list[WorkoutSetLog]:
        statement = (
            select(WorkoutSetLogModel)
            .where(WorkoutSetLogModel.workout_log_id == workout_log_id)
            .order_by(
                WorkoutSetLogModel.workout_plan_exercise_id.asc(),
                WorkoutSetLogModel.set_number.asc(),
            )
        )
        result = await self.session.execute(statement)
        return [
            workout_set_log_model_to_domain(model) for model in result.scalars().all()
        ]

    async def complete_workout_log(self, workout_log: WorkoutLog) -> WorkoutLog:
        statement = select(WorkoutLogModel).where(WorkoutLogModel.id == workout_log.id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Workout log not found during completion.")

        model.completed_at = workout_log.completed_at
        model.duration_minutes = workout_log.duration_minutes
        model.total_volume = workout_log.total_volume
        model.calories_burned = workout_log.calories_burned
        model.avg_heart_rate = workout_log.avg_heart_rate
        model.notes = workout_log.notes
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return workout_log_model_to_domain(model)

    async def create_or_update_feedback(
        self, feedback: WorkoutFeedback
    ) -> WorkoutFeedback:
        statement = select(WorkoutFeedbackModel).where(
            WorkoutFeedbackModel.workout_log_id == feedback.workout_log_id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if model is None:
            model = WorkoutFeedbackModel(
                id=feedback.id,
                workout_log_id=feedback.workout_log_id,
                created_at=now,
            )
            self.session.add(model)

        model.difficulty_feedback = (
            feedback.difficulty_feedback.value
            if feedback.difficulty_feedback is not None
            else None
        )
        model.energy_after = feedback.energy_after
        model.comments = feedback.comments
        model.updated_at = now
        await self.session.flush()
        return workout_feedback_model_to_domain(model)

    async def get_history(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        status: str | None,
        from_date: date_type | None,
        to_date: date_type | None,
    ) -> tuple[list[WorkoutHistoryItem], int]:
        feedback_subquery = select(
            WorkoutFeedbackModel.workout_log_id.label("feedback_workout_log_id"),
            WorkoutFeedbackModel.difficulty_feedback.label("difficulty_feedback"),
        ).subquery()

        base = (
            select(
                WorkoutPlanModel,
                WorkoutLogModel,
                feedback_subquery.c.difficulty_feedback,
            )
            .select_from(WorkoutPlanModel)
            .join(
                WorkoutLogModel,
                and_(
                    WorkoutLogModel.workout_plan_id == WorkoutPlanModel.id,
                    WorkoutLogModel.user_id == WorkoutPlanModel.user_id,
                ),
                isouter=True,
            )
            .join(
                feedback_subquery,
                feedback_subquery.c.feedback_workout_log_id == WorkoutLogModel.id,
                isouter=True,
            )
            .where(WorkoutPlanModel.user_id == user_id)
        )

        if status is not None:
            base = base.where(WorkoutPlanModel.status == status)
        if from_date is not None:
            base = base.where(WorkoutPlanModel.target_date >= from_date)
        if to_date is not None:
            base = base.where(WorkoutPlanModel.target_date <= to_date)

        count_statement = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_statement)).scalar_one()

        statement = (
            base.order_by(
                WorkoutLogModel.completed_at.desc().nullslast(),
                WorkoutPlanModel.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        items = []
        for plan_model, log_model, difficulty_feedback in result.all():
            items.append(
                WorkoutHistoryItem(
                    workout_id=plan_model.id,
                    workout_log_id=log_model.id if log_model else None,
                    title=plan_model.title,
                    date=plan_model.target_date,
                    status=plan_model.status,
                    duration_minutes=log_model.duration_minutes if log_model else None,
                    total_volume=log_model.total_volume if log_model else 0,
                    difficulty_feedback=difficulty_feedback,
                    focus_muscle=plan_model.focus,
                    training_decision=plan_model.decision,
                    source=plan_model.source,
                )
            )
        return items, total
