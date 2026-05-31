from uuid import UUID, uuid4

from src.application.workout.commands import (
    CompleteWorkoutCommand,
    GenerateWorkoutCommand,
    LogWorkoutSetCommand,
    StartWorkoutCommand,
)
from src.application.workout.dto import (
    CompleteWorkoutDTO,
    SetLogDTO,
    StartWorkoutDTO,
    WorkoutExerciseDTO,
    WorkoutHistoryDTO,
    WorkoutHistoryItemDTO,
    WorkoutPlanDTO,
    WorkoutSetLogDTO,
)
from src.application.workout.queries import GetWorkoutDetailQuery, GetWorkoutHistoryQuery
from src.domain.common.enums import (
    DifficultyFeedback,
    EquipmentType,
    MuscleGroup,
    WorkoutDecision,
    WorkoutStatus,
)
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.exercise.entities import Exercise
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.user.repositories import UserRepository
from src.domain.workout.entities import WorkoutFeedback, WorkoutLog, WorkoutSetLog
from src.domain.workout.repositories import WorkoutRepository
from src.domain.workout.services import (
    RuleBasedWorkoutGenerator,
    WorkoutSafetyPolicy,
    WorkoutVolumeCalculator,
)


class GenerateWorkoutUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        readiness_repository: ReadinessRepository,
        exercise_repository: ExerciseRepository,
        workout_repository: WorkoutRepository,
        generator: RuleBasedWorkoutGenerator,
        safety_policy: WorkoutSafetyPolicy,
    ) -> None:
        self.user_repository = user_repository
        self.readiness_repository = readiness_repository
        self.exercise_repository = exercise_repository
        self.workout_repository = workout_repository
        self.generator = generator
        self.safety_policy = safety_policy

    async def execute(self, command: GenerateWorkoutCommand) -> WorkoutPlanDTO:
        profile = await self.user_repository.get_profile(command.user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")

        readiness = await self.readiness_repository.get_by_date(
            command.user_id, command.target_date
        )
        if readiness is None:
            raise NotFoundError("Readiness score not found.")

        equipment = command.equipment or [
            item.equipment_type.value
            for item in await self.user_repository.get_equipment(command.user_id)
        ]
        if not equipment:
            equipment = [EquipmentType.BODYWEIGHT.value]

        allowed = await self.exercise_repository.find_allowed(
            equipment=equipment,
            focus_muscle=command.focus_muscle,
            level=profile.training_level.value,
            limit=50,
        )
        if not allowed:
            allowed = await self.exercise_repository.find_allowed(
                equipment=[
                    EquipmentType.BODYWEIGHT.value,
                    EquipmentType.TREADMILL.value,
                    EquipmentType.RESISTANCE_BAND.value,
                ],
                focus_muscle=None,
                level=profile.training_level.value,
                limit=50,
            )
        if not allowed:
            raise ValidationError("Workout generation failed: no exercises found.")

        plan = self.generator.generate(
            user_id=command.user_id,
            goal=profile.primary_goal.value,
            training_level=profile.training_level.value,
            readiness_score=int(round(readiness.score)),
            readiness_recommendation=readiness.recommendation.value,
            focus_muscle=command.focus_muscle,
            available_time_minutes=command.available_time_minutes,
            exercises=allowed,
            avoid_exercises=command.avoid_exercises,
        )
        plan.target_date = command.target_date
        self.safety_policy.validate(plan, readiness_score=readiness.score)
        saved = await self.workout_repository.save_plan(plan)

        exercise_map = {exercise.id: exercise for exercise in allowed}
        return self._to_plan_dto(saved, exercise_map)

    def _to_plan_dto(
        self, plan, exercise_map: dict[UUID, Exercise]
    ) -> WorkoutPlanDTO:
        return WorkoutPlanDTO(
            workout_id=plan.id,
            workout_log_id=plan.workout_log_id,
            title=plan.title,
            goal=plan.goal.value,
            focus_muscle=plan.focus.value,
            estimated_duration_minutes=plan.estimated_duration_minutes,
            training_decision=plan.decision,
            ai_reasoning_summary=plan.ai_reasoning_summary,
            safety_note=plan.safety_note,
            status=plan.status.value,
            source=plan.source.value,
            exercises=[
                self._to_exercise_dto(item, exercise_map.get(item.exercise_id))
                for item in plan.exercises
            ],
        )

    def _to_exercise_dto(
        self, item, exercise: Exercise | None
    ) -> WorkoutExerciseDTO:
        return WorkoutExerciseDTO(
            workout_plan_exercise_id=item.id,
            exercise_id=item.exercise_id,
            name=(item.name or exercise.name) if exercise else (item.name or "Unknown Exercise"),
            order_index=item.order_index,
            primary_muscle=(item.primary_muscle or exercise.muscle_group.value)
            if exercise
            else (item.primary_muscle or MuscleGroup.FULL_BODY.value),
            equipment=(item.equipment or exercise.equipment_type.value)
            if exercise
            else (item.equipment or EquipmentType.BODYWEIGHT.value),
            target_sets=item.target_sets,
            target_reps=item.target_reps,
            target_weight=item.target_weight,
            rest_seconds=item.rest_seconds,
            target_rpe=item.target_rpe,
            notes=item.notes,
            logged_sets=[
                WorkoutSetLogDTO(
                    set_log_id=logged.id,
                    set_number=logged.set_number,
                    weight=logged.weight_kg,
                    reps=logged.reps_completed,
                    rpe=logged.rpe,
                    completed=logged.completed,
                )
                for logged in item.logged_sets
            ],
        )


class GetWorkoutDetailUseCase:
    def __init__(self, workout_repository: WorkoutRepository) -> None:
        self.workout_repository = workout_repository

    async def execute(self, query: GetWorkoutDetailQuery) -> WorkoutPlanDTO:
        plan = await self.workout_repository.get_plan_detail_by_id(query.workout_id)
        if plan is None or plan.user_id != query.user_id:
            raise NotFoundError("Workout not found.")

        latest_log = await self.workout_repository.get_latest_log_by_plan_id(
            query.user_id, query.workout_id
        )
        if latest_log is not None:
            plan.workout_log_id = latest_log.id
            set_logs = await self.workout_repository.get_set_logs_by_workout_log_id(
                latest_log.id
            )
            by_exercise: dict[UUID, list[WorkoutSetLog]] = {}
            for set_log in set_logs:
                by_exercise.setdefault(set_log.workout_plan_exercise_id, []).append(set_log)
            for exercise in plan.exercises:
                exercise.logged_sets = by_exercise.get(exercise.id, [])

        return WorkoutPlanDTO(
            workout_id=plan.id,
            workout_log_id=plan.workout_log_id,
            title=plan.title,
            goal=plan.goal.value,
            focus_muscle=plan.focus.value,
            estimated_duration_minutes=plan.estimated_duration_minutes,
            training_decision=plan.decision,
            ai_reasoning_summary=plan.ai_reasoning_summary,
            safety_note=plan.safety_note,
            status=plan.status.value,
            source=plan.source.value,
            exercises=[
                WorkoutExerciseDTO(
                    workout_plan_exercise_id=item.id,
                    exercise_id=item.exercise_id,
                    name=item.name or "Unknown Exercise",
                    order_index=item.order_index,
                    primary_muscle=item.primary_muscle or MuscleGroup.FULL_BODY.value,
                    equipment=item.equipment or EquipmentType.BODYWEIGHT.value,
                    target_sets=item.target_sets,
                    target_reps=item.target_reps,
                    target_weight=item.target_weight,
                    rest_seconds=item.rest_seconds,
                    target_rpe=item.target_rpe,
                    notes=item.notes,
                    logged_sets=[
                        WorkoutSetLogDTO(
                            set_log_id=set_log.id,
                            set_number=set_log.set_number,
                            weight=set_log.weight_kg,
                            reps=set_log.reps_completed,
                            rpe=set_log.rpe,
                            completed=set_log.completed,
                        )
                        for set_log in item.logged_sets
                    ],
                )
                for item in plan.exercises
            ],
        )


class StartWorkoutUseCase:
    def __init__(self, workout_repository: WorkoutRepository) -> None:
        self.workout_repository = workout_repository

    async def execute(self, command: StartWorkoutCommand) -> StartWorkoutDTO:
        plan = await self.workout_repository.get_plan_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")
        if plan.status == WorkoutStatus.COMPLETED:
            raise ValidationError("Workout is already completed.")

        active_log = await self.workout_repository.get_active_log_by_plan_id(
            command.user_id, command.workout_id
        )
        if active_log is not None:
            if plan.status != WorkoutStatus.STARTED:
                plan.start()
                await self.workout_repository.update_plan(plan)
            return StartWorkoutDTO(
                workout_id=plan.id,
                workout_log_id=active_log.id,
                status=WorkoutStatus.STARTED.value,
                started_at=active_log.started_at,
            )

        plan.start()
        await self.workout_repository.update_plan(plan)
        log = await self.workout_repository.create_workout_log(
            user_id=command.user_id,
            workout_plan_id=command.workout_id,
            started_at=command.started_at,
        )
        return StartWorkoutDTO(
            workout_id=plan.id,
            workout_log_id=log.id,
            status=plan.status.value,
            started_at=log.started_at,
        )


class LogWorkoutSetUseCase:
    def __init__(self, workout_repository: WorkoutRepository) -> None:
        self.workout_repository = workout_repository

    async def execute(self, command: LogWorkoutSetCommand) -> SetLogDTO:
        plan = await self.workout_repository.get_plan_detail_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")
        if plan.status != WorkoutStatus.STARTED:
            raise ValidationError("Workout must be started before logging sets.")

        log = await self.workout_repository.get_workout_log_by_id(command.workout_log_id)
        if log is None or log.user_id != command.user_id or log.workout_plan_id != command.workout_id:
            raise NotFoundError("Workout log not found.")

        plan_exercise = next(
            (item for item in plan.exercises if item.id == command.workout_plan_exercise_id),
            None,
        )
        if plan_exercise is None:
            raise NotFoundError("Workout exercise not found in plan.")

        saved = await self.workout_repository.upsert_set_log(
            WorkoutSetLog(
                id=uuid4(),
                workout_log_id=command.workout_log_id,
                workout_plan_exercise_id=command.workout_plan_exercise_id,
                set_number=command.set_number,
                reps_completed=command.reps,
                weight_kg=command.weight,
                rpe=command.rpe,
                completed=command.completed,
            )
        )
        return SetLogDTO(
            set_log_id=saved.id,
            workout_log_id=saved.workout_log_id,
            workout_plan_exercise_id=saved.workout_plan_exercise_id,
            set_number=saved.set_number,
        )


class CompleteWorkoutUseCase:
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        volume_calculator: WorkoutVolumeCalculator,
    ) -> None:
        self.workout_repository = workout_repository
        self.volume_calculator = volume_calculator

    async def execute(self, command: CompleteWorkoutCommand) -> CompleteWorkoutDTO:
        plan = await self.workout_repository.get_plan_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")

        log = await self.workout_repository.get_workout_log_by_id(command.workout_log_id)
        if log is None or log.user_id != command.user_id or log.workout_plan_id != command.workout_id:
            raise NotFoundError("Workout log not found.")

        if plan.status == WorkoutStatus.COMPLETED and log.completed_at is not None:
            return CompleteWorkoutDTO(
                workout_id=plan.id,
                workout_log_id=log.id,
                status=WorkoutStatus.COMPLETED.value,
                total_volume=log.total_volume,
                completed_at=log.completed_at,
            )
        if plan.status != WorkoutStatus.STARTED:
            raise ValidationError("Workout must be started before completion.")

        set_logs = await self.workout_repository.get_set_logs_by_workout_log_id(log.id)
        total_volume = self.volume_calculator.calculate_total_volume(set_logs)

        log.completed_at = command.completed_at
        log.duration_minutes = command.duration_minutes
        log.total_volume = total_volume
        log.calories_burned = command.calories_burned
        log.avg_heart_rate = command.avg_heart_rate
        log.notes = command.notes
        log = await self.workout_repository.complete_workout_log(log)

        if (
            command.difficulty_feedback is not None
            or command.energy_after is not None
            or command.notes is not None
        ):
            feedback_enum = (
                DifficultyFeedback(command.difficulty_feedback)
                if command.difficulty_feedback is not None
                else None
            )
            await self.workout_repository.create_or_update_feedback(
                WorkoutFeedback(
                    id=uuid4(),
                    workout_log_id=log.id,
                    difficulty_feedback=feedback_enum,
                    energy_after=command.energy_after,
                    comments=command.notes,
                )
            )

        plan.complete()
        await self.workout_repository.update_plan(plan)

        return CompleteWorkoutDTO(
            workout_id=plan.id,
            workout_log_id=log.id,
            status=plan.status.value,
            total_volume=total_volume,
            completed_at=log.completed_at,
        )


class GetWorkoutHistoryUseCase:
    def __init__(self, workout_repository: WorkoutRepository) -> None:
        self.workout_repository = workout_repository

    async def execute(self, query: GetWorkoutHistoryQuery) -> WorkoutHistoryDTO:
        items, total = await self.workout_repository.get_history(
            user_id=query.user_id,
            limit=query.limit,
            offset=query.offset,
            status=query.status,
            from_date=query.from_date,
            to_date=query.to_date,
        )
        return WorkoutHistoryDTO(
            items=[
                WorkoutHistoryItemDTO(
                    workout_id=item.workout_id,
                    workout_log_id=item.workout_log_id,
                    title=item.title,
                    date=item.date,
                    status=item.status,
                    duration_minutes=item.duration_minutes,
                    total_volume=item.total_volume,
                    difficulty_feedback=item.difficulty_feedback,
                    focus_muscle=item.focus_muscle,
                    training_decision=item.training_decision,
                    source=item.source,
                )
                for item in items
            ],
            limit=query.limit,
            offset=query.offset,
            total=total,
        )
