import logging
from datetime import datetime, timezone
from time import perf_counter
from uuid import UUID, uuid4

from app.settings import get_settings
from src.application.ai_usage.commands import (
    CheckAIUsageLimitCommand,
    RecordAIUsageCommand,
)
from src.application.ai_usage.use_cases import AIUsageService
from src.domain.ai.entities import (
    AIAllowedExercise,
    AIProgressionContext,
    AIRequestLog,
    AIWorkoutGenerationContext,
)
from src.domain.ai.ports import AIWorkoutGeneratorPort
from src.application.workout.commands import (
    ApplyExerciseReplacementCommand,
    CompleteWorkoutCommand,
    GenerateWorkoutCommand,
    LogWorkoutSetCommand,
    SuggestExerciseReplacementCommand,
    StartWorkoutCommand,
)
from src.application.workout.dto import (
    ApplyExerciseReplacementDTO,
    CompleteWorkoutDTO,
    ReplacementCurrentExerciseDTO,
    ReplacementOptionDTO,
    SetLogDTO,
    StartWorkoutDTO,
    SuggestExerciseReplacementDTO,
    WorkoutExerciseDTO,
    WorkoutHistoryDTO,
    WorkoutHistoryItemDTO,
    WorkoutPlanDTO,
    WorkoutSetLogDTO,
)
from src.application.workout.queries import (
    GetWorkoutDetailQuery,
    GetWorkoutHistoryQuery,
)
from src.domain.common.enums import (
    DifficultyFeedback,
    EquipmentType,
    MuscleGroup,
    ReadinessCategory,
    ReadinessRecommendation,
    WorkoutDecision,
    WorkoutStatus,
)
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.common.exceptions import (
    AIConfigurationError,
    AIExerciseMappingError,
    AIGenerationError,
    AIInvalidOutputError,
    AIProviderTimeoutError,
    AIRateLimitError,
    AIUsageLimitExceededError,
    AIUnsafeOutputError,
)
from src.domain.exercise.entities import Exercise
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.progression.entities import ExercisePerformanceHistory
from src.domain.progression.repositories import ProgressionRepository
from src.domain.program.entities import ProgramWorkoutStatus
from src.domain.program.repositories import ProgramRepository
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.training.entities import TrainingRecommendationContext
from src.domain.training.services import TrainingRecommendationService
from src.domain.user.repositories import UserRepository
from src.domain.workout.entities import WorkoutFeedback, WorkoutLog, WorkoutSetLog
from src.domain.workout.repositories import WorkoutRepository
from src.domain.workout.services import (
    RuleBasedWorkoutGenerator,
    WorkoutSafetyPolicy,
    WorkoutVolumeCalculator,
)
from src.domain.exercise.equipment_policy import get_equipment_category
from src.domain.workout.workout_volume_policy import WorkoutVolumePolicy
from src.infrastructure.ai.output_mapper import AIWorkoutOutputMapper
from src.infrastructure.ai.safety_validator import AIWorkoutSafetyValidator

logger = logging.getLogger(__name__)
AI_ALLOWED_EXERCISES_LIMIT = 16


class _ReadinessSnapshot:
    def __init__(
        self,
        score: float = 75.0,
        category: ReadinessCategory = ReadinessCategory.GOOD,
        recommendation: ReadinessRecommendation = ReadinessRecommendation.TRAIN_NORMAL,
    ) -> None:
        self.score = score
        self.category = category
        self.recommendation = recommendation


class GenerateWorkoutUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        readiness_repository: ReadinessRepository,
        exercise_repository: ExerciseRepository,
        workout_repository: WorkoutRepository,
        generator: RuleBasedWorkoutGenerator,
        ai_generator: AIWorkoutGeneratorPort,
        ai_usage_service: AIUsageService,
        ai_safety_validator: AIWorkoutSafetyValidator,
        ai_output_mapper: AIWorkoutOutputMapper,
        safety_policy: WorkoutSafetyPolicy,
        training_service: TrainingRecommendationService | None = None,
        progression_repository: ProgressionRepository | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.readiness_repository = readiness_repository
        self.exercise_repository = exercise_repository
        self.workout_repository = workout_repository
        self.generator = generator
        self.ai_generator = ai_generator
        self.ai_usage_service = ai_usage_service
        self.ai_safety_validator = ai_safety_validator
        self.ai_output_mapper = ai_output_mapper
        self.safety_policy = safety_policy
        self.training_service = training_service
        self.progression_repository = progression_repository
        self.volume_policy = WorkoutVolumePolicy()

    async def execute(self, command: GenerateWorkoutCommand) -> WorkoutPlanDTO:
        profile = await self.user_repository.get_profile(command.user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")

        readiness = await self.readiness_repository.get_by_date(
            command.user_id, command.target_date
        )
        if readiness is None:
            if command.allow_missing_readiness:
                readiness = _ReadinessSnapshot()
            else:
                raise NotFoundError("Readiness score not found.")

        equipment = command.equipment or [
            item.equipment_type.value
            for item in await self.user_repository.get_equipment(command.user_id)
        ]
        if not equipment:
            equipment = [EquipmentType.BODYWEIGHT.value]

        allowed = await self.exercise_repository.find_allowed(
            equipment=equipment,
            focus_muscle=None,
            level=profile.training_level.value,
            limit=100,
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
                limit=100,
            )
        if not allowed:
            raise ValidationError("Workout generation failed: no exercises found.")

        usage_date = self._usage_date()
        ai_input_payload = {
            "readiness_score": int(round(readiness.score)),
            "readiness_category": readiness.category.value,
            "equipment": equipment,
            "workout_split": command.workout_split,
            "focus_muscle": command.focus_muscle,
            "allowed_exercise_slugs": [item.slug for item in allowed[:16]],
        }
        training_context = await self._build_training_context(command)
        recent_workouts = await self._build_recent_workouts(command)
        progression_histories = await self._build_progression_histories(
            command.user_id, allowed
        )
        if training_context is not None:
            ai_input_payload["training_context"] = self._training_context_payload(
                training_context
            )

        goal = command.goal_override or profile.primary_goal.value
        training_style = self._effective_training_style(
            profile,
            command.training_style_override or profile.training_style.value,
            has_explicit_override=command.training_style_override is not None,
        )
        if command.generation_mode == "rule_based":
            plan = self._generate_rule_based(
                command,
                goal,
                profile.training_level.value,
                readiness.score,
                readiness.recommendation.value,
                allowed,
                equipment,
                profile.injuries,
                training_context,
                recent_workouts,
                progression_histories,
                training_style,
                profile,
            )
        elif command.generation_mode in {"gemini", "openrouter"}:
            try:
                await self.ai_usage_service.check_limit(
                    CheckAIUsageLimitCommand(
                        user_id=command.user_id,
                        request_type="generate_workout",
                        target_date=usage_date,
                    )
                )
            except AIUsageLimitExceededError as exc:
                await self.ai_usage_service.record_log_only(
                    self._build_ai_request_log(
                        request_id=uuid4(),
                        command=command,
                        status="blocked",
                        input_payload=ai_input_payload,
                        error_code="AI_LIMIT_REACHED",
                        error_message=str(exc),
                        fallback_used=False,
                        latency_ms=0,
                    )
                )
                raise
            plan = await self._generate_with_ai_with_logging(
                command=command,
                goal=goal,
                training_level=profile.training_level.value,
                readiness=readiness,
                equipment=equipment,
                allowed=allowed,
                usage_date=usage_date,
                input_payload=ai_input_payload,
                training_context=training_context,
                profile=profile,
                progression_histories=progression_histories,
                training_style=training_style,
            )
        else:
            try:
                await self.ai_usage_service.check_limit(
                    CheckAIUsageLimitCommand(
                        user_id=command.user_id,
                        request_type="generate_workout",
                        target_date=usage_date,
                    )
                )
                plan = await self._generate_with_ai_with_logging(
                    command=command,
                    goal=goal,
                    training_level=profile.training_level.value,
                    readiness=readiness,
                    equipment=equipment,
                    allowed=allowed,
                    usage_date=usage_date,
                    input_payload=ai_input_payload,
                    training_context=training_context,
                    profile=profile,
                    progression_histories=progression_histories,
                    training_style=training_style,
                )
            except AIUsageLimitExceededError as exc:
                logger.error(
                    "AI usage limit exceeded for user %s, falling back to rule-based generation. Error: %s",
                    command.user_id,
                    exc,
                )
                await self.ai_usage_service.record_log_only(
                    self._build_ai_request_log(
                        request_id=uuid4(),
                        command=command,
                        status="blocked",
                        input_payload=ai_input_payload,
                        error_code="AI_LIMIT_REACHED",
                        error_message=str(exc),
                        fallback_used=True,
                        latency_ms=0,
                    )
                )
                plan = self._generate_rule_based(
                    command,
                    goal,
                    profile.training_level.value,
                    readiness.score,
                    readiness.recommendation.value,
                    allowed,
                    equipment,
                    profile.injuries,
                    training_context,
                    recent_workouts,
                    progression_histories,
                    training_style,
                    profile,
                )
            except (
                AIConfigurationError,
                AIGenerationError,
                AIRateLimitError,
                AIProviderTimeoutError,
                AIInvalidOutputError,
                AIUnsafeOutputError,
                AIExerciseMappingError,
                Exception,
            ) as exc:
                print(
                    f"\n\n[WARNING] AI WORKOUT GENERATION FAILED, FALLING BACK TO RULE-BASED. ERROR: {exc}\n\n",
                    flush=True,
                )
                logger.exception(
                    "AI workout generation failed for user %s mode=%s, falling back to rule-based. error_type=%s error=%s input_payload=%s",
                    command.user_id,
                    command.generation_mode,
                    exc.__class__.__name__,
                    exc,
                    ai_input_payload,
                )
                plan = self._generate_rule_based(
                    command,
                    goal,
                    profile.training_level.value,
                    readiness.score,
                    readiness.recommendation.value,
                    allowed,
                    equipment,
                    profile.injuries,
                    training_context,
                    recent_workouts,
                    progression_histories,
                    training_style,
                    profile,
                )
        plan.target_date = command.target_date
        self.safety_policy.validate(
            plan, readiness_score=plan.readiness_score or readiness.score
        )
        saved = await self.workout_repository.save_plan(plan)

        exercise_map = {exercise.id: exercise for exercise in allowed}
        return self._to_plan_dto(saved, exercise_map)

    def _to_plan_dto(self, plan, exercise_map: dict[UUID, Exercise]) -> WorkoutPlanDTO:
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

    def _generate_rule_based(
        self,
        command: GenerateWorkoutCommand,
        goal: str,
        training_level: str,
        readiness_score: float,
        readiness_recommendation: str,
        allowed: list[Exercise],
        equipment: list[str],
        injuries: list[str],
        training_context: TrainingRecommendationContext | None = None,
        recent_workouts=None,
        progression_histories: dict[UUID, ExercisePerformanceHistory] | None = None,
        training_style: str = "balanced",
        profile=None,
    ):
        return self.generator.generate(
            user_id=command.user_id,
            goal=goal,
            training_level=training_level,
            readiness_score=int(round(readiness_score)),
            readiness_recommendation=readiness_recommendation,
            workout_split=command.workout_split,
            focus_muscle=command.focus_muscle,
            available_time_minutes=command.available_time_minutes,
            exercises=allowed,
            avoid_exercises=command.avoid_exercises,
            available_equipment=equipment,
            injuries=injuries,
            training_context=training_context,
            target_date=command.target_date,
            recent_workouts=recent_workouts,
            progression_histories=progression_histories,
            training_style=training_style,
            movement_limitations=profile.movement_limitations if profile else [],
            pain_areas=profile.pain_areas if profile else [],
            pain_movements=profile.pain_movements if profile else [],
            lifestyle_type=profile.lifestyle_type if profile else None,
            sitting_hours_per_day=profile.sitting_hours_per_day if profile else None,
            training_history=profile.training_history if profile else None,
            months_inactive=profile.months_inactive if profile else None,
        )

    async def _generate_with_ai(
        self,
        command: GenerateWorkoutCommand,
        goal: str,
        training_level: str,
        readiness,
        equipment: list[str],
        allowed: list[Exercise],
        training_context: TrainingRecommendationContext | None = None,
        profile=None,
        progression_histories: dict[UUID, ExercisePerformanceHistory] | None = None,
        training_style: str = "balanced",
    ):
        effective_focus = command.focus_muscle
        if effective_focus is None and training_context is not None:
            effective_focus = training_context.suggested_focus
        ai_allowed = self._select_ai_allowed_exercises(
            allowed=allowed,
            focus_muscle=effective_focus,
            workout_split=command.workout_split,
            avoid_exercises=command.avoid_exercises,
        )
        target_min, target_max = self.volume_policy.target_exercise_count(
            training_level,
            command.available_time_minutes,
            training_style,
            readiness.score,
        )
        context = AIWorkoutGenerationContext(
            user_id=command.user_id,
            target_date=command.target_date,
            goal=goal,
            training_level=training_level,
            readiness_score=int(round(readiness.score)),
            readiness_category=readiness.category.value,
            readiness_recommendation=readiness.recommendation.value,
            workout_split=command.workout_split,
            focus_muscle=effective_focus,
            available_time_minutes=command.available_time_minutes,
            equipment=equipment,
            avoid_exercises=command.avoid_exercises,
            allowed_exercises=[
                AIAllowedExercise(
                    exercise_id=item.id,
                    name=item.name,
                    slug=item.slug,
                    primary_muscle=item.muscle_group.value,
                    equipment=item.equipment_type.value,
                    difficulty=item.training_level.value,
                    movement_type=item.movement_type,
                    movement_pattern=item.movement_pattern,
                    exercise_role=item.exercise_role,
                )
                for item in ai_allowed
            ],
            user_note=command.user_note,
            injuries=list(profile.injuries) if profile else [],
            movement_limitations=list(profile.movement_limitations) if profile else [],
            pain_areas=list(profile.pain_areas) if profile else [],
            pain_movements=list(profile.pain_movements) if profile else [],
            lifestyle_type=profile.lifestyle_type if profile else None,
            sitting_hours_per_day=profile.sitting_hours_per_day if profile else None,
            training_history=profile.training_history if profile else None,
            months_inactive=profile.months_inactive if profile else None,
            training_style=training_style,
            target_exercise_count_min=target_min,
            target_exercise_count_max=target_max,
            role_distribution=self.volume_policy.target_role_distribution(
                training_level,
                command.available_time_minutes,
                training_style,
                readiness.score,
            ),
            movement_pattern_requirements=self._available_movement_requirements(
                self._movement_pattern_requirements(
                    effective_focus, command.workout_split
                ),
                ai_allowed,
            ),
            equipment_mix_requirements=self._equipment_mix_requirements(
                equipment, ai_allowed
            ),
            ordering_guidelines=[
                "warmup/activation",
                "main compound",
                "secondary compound",
                "accessory",
                "isolation",
                "corrective",
                "core",
                "cardio finisher",
                "cooldown/mobility last",
            ],
            progression_context=self._progression_context(
                ai_allowed,
                progression_histories,
                training_level,
                int(round(readiness.score)),
            ),
        )
        logger.info(
            "Prepared AI workout context for user %s readiness=%s/%s recommendation=%s focus=%s time=%s equipment=%s allowed_slugs=%s",
            command.user_id,
            context.readiness_score,
            context.readiness_category,
            context.readiness_recommendation,
            context.focus_muscle,
            context.available_time_minutes,
            context.equipment,
            [item.slug for item in context.allowed_exercises],
        )
        result = await self.ai_generator.generate_workout(context)
        logger.info(
            "AI workout result before safety validation for user %s title=%s decision=%s duration=%s exercises=%s",
            command.user_id,
            result.workout_title,
            result.training_decision,
            result.estimated_duration_minutes,
            [
                {
                    "slug": item.exercise_slug,
                    "sets": item.sets,
                    "reps": item.reps,
                    "rest_seconds": item.rest_seconds,
                    "rpe": item.rpe,
                }
                for item in result.exercises
            ],
        )
        self.ai_safety_validator.validate(result, context)
        logger.info("AI workout safety validation passed for user %s", command.user_id)
        plan = self.ai_output_mapper.to_workout_plan(result, context)
        logger.info(
            "AI workout mapped to plan for user %s title=%s source=%s exercise_count=%s",
            command.user_id,
            plan.title,
            plan.source.value,
            len(plan.exercises),
        )
        return plan

    async def _generate_with_ai_with_logging(
        self,
        command: GenerateWorkoutCommand,
        goal: str,
        training_level: str,
        readiness,
        equipment: list[str],
        allowed: list[Exercise],
        usage_date,
        input_payload: dict,
        training_context: TrainingRecommendationContext | None = None,
        profile=None,
        progression_histories: dict[UUID, ExercisePerformanceHistory] | None = None,
        training_style: str = "balanced",
    ):
        request_id = uuid4()
        started = perf_counter()
        try:
            plan = await self._generate_with_ai(
                command,
                goal,
                training_level,
                readiness,
                equipment,
                allowed,
                training_context,
                profile,
                progression_histories,
                training_style,
            )
        except (
            AIConfigurationError,
            AIGenerationError,
            AIRateLimitError,
            AIProviderTimeoutError,
            AIInvalidOutputError,
            AIUnsafeOutputError,
            AIExerciseMappingError,
            Exception,
        ) as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            print(
                f"\n\n[WARNING] AI WORKOUT GENERATION FAILED (mode={command.generation_mode}). ERROR: {exc}\n\n",
                flush=True,
            )
            logger.exception(
                "AI workout generation failed for user %s mode=%s latency_ms=%s error_type=%s error=%s input_payload=%s",
                command.user_id,
                command.generation_mode,
                latency_ms,
                exc.__class__.__name__,
                exc,
                input_payload,
            )
            await self.ai_usage_service.record(
                RecordAIUsageCommand(
                    user_id=command.user_id,
                    request_type="generate_workout",
                    target_date=usage_date,
                    request_log=self._build_ai_request_log(
                        request_id=request_id,
                        command=command,
                        status=(
                            "fallback_used"
                            if command.generation_mode == "auto"
                            else "failed"
                        ),
                        input_payload=input_payload,
                        output_payload={},
                        error_code=exc.__class__.__name__,
                        error_message=str(exc),
                        fallback_used=command.generation_mode == "auto",
                        latency_ms=latency_ms,
                    ),
                )
            )
            raise

        latency_ms = int((perf_counter() - started) * 1000)
        output_payload = {
            "title": plan.title,
            "training_decision": plan.decision,
            "exercise_ids": [str(item.exercise_id) for item in plan.exercises],
            "exercise_count": len(plan.exercises),
        }
        await self.ai_usage_service.record(
            RecordAIUsageCommand(
                user_id=command.user_id,
                request_type="generate_workout",
                target_date=usage_date,
                request_log=self._build_ai_request_log(
                    request_id=request_id,
                    command=command,
                    status="success",
                    input_payload=input_payload,
                    output_payload=output_payload,
                    fallback_used=False,
                    latency_ms=latency_ms,
                ),
            )
        )
        logger.info(
            "AI workout generation succeeded for user %s mode=%s latency_ms=%s output_payload=%s",
            command.user_id,
            command.generation_mode,
            latency_ms,
            output_payload,
        )
        return plan

    async def _build_training_context(
        self, command: GenerateWorkoutCommand
    ) -> TrainingRecommendationContext | None:
        if self.training_service is None:
            return None
        return await self.training_service.build_context(
            command.user_id, command.target_date
        )

    async def _build_recent_workouts(self, command: GenerateWorkoutCommand):
        items, _ = await self.workout_repository.get_history(
            user_id=command.user_id,
            limit=3,
            offset=0,
            status=None,
            from_date=None,
            to_date=command.target_date,
        )
        return items

    async def _build_progression_histories(
        self, user_id: UUID, exercises: list[Exercise]
    ) -> dict[UUID, ExercisePerformanceHistory] | None:
        if self.progression_repository is None:
            return None
        return await self.progression_repository.get_recent_performance_for_exercises(
            user_id=user_id,
            exercise_ids=[item.id for item in exercises],
            limit_per_exercise=3,
        )

    def _training_context_payload(self, context: TrainingRecommendationContext) -> dict:
        return {
            "load_score": context.recent_load.load_score,
            "load_level": context.recent_load.load_level,
            "suggested_focus": context.suggested_focus,
            "avoid_focus": context.avoid_focus,
            "reason": context.reason,
        }

    def _effective_training_style(
        self, profile, requested_style: str, *, has_explicit_override: bool
    ) -> str:
        if has_explicit_override:
            return requested_style
        history = (profile.training_history or "").strip().lower()
        if (
            "returning" in history
            or "after_break" in history
            or (profile.months_inactive or 0) >= 3
        ):
            return "returning"
        lifestyle = (profile.lifestyle_type or "").strip().lower()
        if requested_style == "balanced" and (
            lifestyle in {"sedentary", "desk_job", "desk_worker"}
            or (profile.sitting_hours_per_day or 0) >= 8
        ):
            return "posture"
        return requested_style

    def _movement_pattern_requirements(
        self, focus_muscle: str | None, workout_split: str
    ) -> list[str]:
        focus = (focus_muscle or workout_split or "full_body").lower()
        if focus in {
            "upper_body_pull",
            "pull",
            "back",
            "upper_pull_posture",
            "upper_pull_focus",
        }:
            return ["horizontal_pull", "vertical_pull"]
        if focus in {
            "upper_body_push",
            "push",
            "chest",
            "upper_push_balanced",
            "upper_push_focus",
        }:
            return ["horizontal_push", "vertical_push"]
        if focus in {
            "lower_body",
            "legs",
            "lower_core",
            "lower_posterior_core",
            "lower_quad_core",
        }:
            return ["squat", "hinge"]
        if focus == "upper_arms_shoulders":
            return [
                "vertical_pull",
                "vertical_push",
                "elbow_flexion",
                "elbow_extension",
            ]
        if focus in {"full_body", "full_body_conditioning"}:
            return ["squat", "hinge", "horizontal_push", "horizontal_pull"]
        if focus == "upper_body":
            return ["horizontal_push", "horizontal_pull"]
        return []

    def _equipment_mix_requirements(
        self, equipment: list[str], exercises: list[Exercise] | None = None
    ) -> list[str]:
        equipment_categories = {get_equipment_category(item) for item in equipment} - {
            "other"
        }
        exercise_categories = {
            get_equipment_category(item.equipment_type.value)
            for item in exercises or []
        } - {"other"}
        categories = (
            equipment_categories & exercise_categories
            if exercises is not None
            else equipment_categories
        )
        if len(categories) < 3:
            return ["Use the available equipment without forced diversity."]
        requirements = ["No equipment category may exceed 60% of exercises."]
        if "free_weight" in categories:
            requirements.append("Prefer at least two free-weight exercises.")
        if categories & {"machine", "cable"}:
            requirements.append("Include at least one machine or cable exercise.")
        requirements.append("Include bodyweight or core work when appropriate.")
        return requirements

    def _available_movement_requirements(
        self, required: list[str], exercises: list[Exercise]
    ) -> list[str]:
        available = {
            (item.movement_pattern or item.movement_type or "").strip().lower()
            for item in exercises
        }
        return [pattern for pattern in required if pattern in available]

    def _progression_context(
        self,
        exercises: list[Exercise],
        histories: dict[UUID, ExercisePerformanceHistory] | None,
        training_level: str,
        readiness_score: int,
    ) -> list[AIProgressionContext]:
        if not histories:
            return []
        result: list[AIProgressionContext] = []
        for exercise in exercises:
            history = histories.get(exercise.id)
            if history is None or not history.recent_sessions:
                continue
            suggestion = self.generator.progression_service.suggest_next_prescription(
                history=history,
                default_sets=3,
                default_reps="8-12",
                default_rpe=7,
                training_level=training_level,
            )
            suggestion = self.generator.progression_service.apply_readiness_guard(
                suggestion, history, readiness_score
            )
            latest = max(history.recent_sessions, key=lambda item: item.completed_at)
            completed = [item for item in latest.sets if item.completed]
            last_performance = ", ".join(
                f"{item.weight or 0:g}kg x {item.reps or 0} @ RPE {item.rpe or '?'}"
                for item in completed
            )
            result.append(
                AIProgressionContext(
                    exercise_slug=exercise.slug,
                    last_performance=last_performance or None,
                    progression_action=suggestion.action.value,
                    suggested_weight=suggestion.suggested_weight,
                    suggested_reps=suggestion.suggested_reps,
                    reason=suggestion.reason,
                )
            )
        return result

    def _select_ai_allowed_exercises(
        self,
        allowed: list[Exercise],
        focus_muscle: str | None,
        workout_split: str,
        avoid_exercises: list[str],
    ) -> list[Exercise]:
        avoid_set = {item.strip().lower() for item in avoid_exercises}
        required_patterns = self._movement_pattern_requirements(
            focus_muscle, workout_split
        )
        focus_muscles = self._focus_muscles(focus_muscle, workout_split)

        def _score(item: Exercise) -> tuple[int, int, int, int, int, str]:
            movement_pattern = self._exercise_movement_pattern(item)
            focus_match = int(item.muscle_group.value in focus_muscles)
            split_match = int(self._matches_workout_split(item, workout_split))
            required_pattern_match = int(movement_pattern in required_patterns)
            compound_bonus = int(
                item.exercise_role in {"main_compound", "secondary_compound"}
            )
            primary_muscle_bonus = int(
                item.muscle_group.value not in {"arms", "core", "mobility", "cardio"}
            )
            return (
                -required_pattern_match,
                -focus_match,
                -split_match,
                -compound_bonus,
                -primary_muscle_bonus,
                item.name,
            )

        filtered = [
            item
            for item in allowed
            if item.slug.lower() not in avoid_set and item.name.lower() not in avoid_set
        ]
        if not filtered:
            return allowed[:AI_ALLOWED_EXERCISES_LIMIT]

        ranked = sorted(filtered, key=_score)
        selected: list[Exercise] = []
        selected_ids: set[UUID] = set()

        def add_candidates(candidates: list[Exercise], limit: int) -> None:
            added = 0
            for candidate in candidates:
                if candidate.id in selected_ids:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.id)
                added += 1
                if added >= limit or len(selected) >= AI_ALLOWED_EXERCISES_LIMIT:
                    break

        # Give the model multiple valid choices for every required movement slot.
        for pattern in required_patterns:
            pattern_candidates = [
                item
                for item in ranked
                if self._exercise_movement_pattern(item) == pattern
            ]
            add_candidates(
                self._prefer_distinct_equipment_categories(pattern_candidates),
                limit=3,
            )

        # Ensure the prompt contains actual alternatives across available categories.
        available_categories = {
            get_equipment_category(item.equipment_type.value) for item in ranked
        } - {"other"}
        for category in (
            "free_weight",
            "machine",
            "cable",
            "bodyweight",
            "cardio",
        ):
            if category not in available_categories:
                continue
            category_candidates = [
                item
                for item in ranked
                if get_equipment_category(item.equipment_type.value) == category
            ]
            add_candidates(category_candidates, limit=2)

        # Preserve role variety so the model can satisfy the ordering policy.
        for roles in (
            {"main_compound", "secondary_compound"},
            {"accessory"},
            {"isolation", "corrective"},
            {"finisher"},
        ):
            add_candidates(
                [item for item in ranked if item.exercise_role in roles],
                limit=2,
            )

        for candidate in ranked:
            if len(selected) >= AI_ALLOWED_EXERCISES_LIMIT:
                break
            category = get_equipment_category(candidate.equipment_type.value)
            if self._shortlist_category_is_full(selected, category):
                continue
            add_candidates([candidate], limit=1)

        if len(selected) < AI_ALLOWED_EXERCISES_LIMIT:
            add_candidates(ranked, AI_ALLOWED_EXERCISES_LIMIT - len(selected))
        return selected[:AI_ALLOWED_EXERCISES_LIMIT]

    def _focus_muscles(self, focus_muscle: str | None, workout_split: str) -> set[str]:
        focus = (focus_muscle or workout_split or "full_body").lower()
        if focus in {
            "upper_body_push",
            "upper_push_balanced",
            "upper_push_focus",
            "push",
            "chest",
        }:
            return {"chest", "shoulders"}
        if focus in {
            "upper_body_pull",
            "upper_pull_posture",
            "upper_pull_focus",
            "pull",
            "back",
        }:
            return {"back", "shoulders"}
        if focus in {
            "lower_body",
            "lower_core",
            "lower_posterior_core",
            "lower_quad_core",
            "legs",
        }:
            return {"legs", "core"}
        if focus == "upper_arms_shoulders":
            return {"back", "shoulders", "arms"}
        if focus == "upper_body":
            return {"chest", "back", "shoulders", "arms"}
        return {"chest", "back", "shoulders", "legs", "core", "full_body"}

    def _exercise_movement_pattern(self, exercise: Exercise) -> str:
        return (exercise.movement_pattern or exercise.movement_type or "").lower()

    def _prefer_distinct_equipment_categories(
        self, candidates: list[Exercise]
    ) -> list[Exercise]:
        categories: list[str] = []
        by_category: dict[str, list[Exercise]] = {}
        for candidate in candidates:
            category = get_equipment_category(candidate.equipment_type.value)
            if category not in by_category:
                categories.append(category)
                by_category[category] = []
            by_category[category].append(candidate)

        result: list[Exercise] = []
        while any(by_category.values()):
            for category in categories:
                if by_category[category]:
                    result.append(by_category[category].pop(0))
        return result

    def _shortlist_category_is_full(
        self, selected: list[Exercise], category: str
    ) -> bool:
        if category == "other":
            return False
        count = sum(
            get_equipment_category(item.equipment_type.value) == category
            for item in selected
        )
        return count >= AI_ALLOWED_EXERCISES_LIMIT // 2

    def _matches_workout_split(self, exercise: Exercise, workout_split: str) -> bool:
        muscle = exercise.muscle_group.value
        movement = self._exercise_movement_pattern(exercise)
        if workout_split == "upper_body":
            return muscle in {"chest", "back", "shoulders", "arms"}
        if workout_split == "lower_body":
            return muscle in {"legs", "core"} or movement in {"squat", "hinge"}
        if workout_split == "push":
            return muscle in {"chest", "shoulders", "arms"} or movement in {
                "horizontal_push",
                "vertical_push",
                "elbow_extension",
            }
        if workout_split == "pull":
            return muscle in {"back", "arms"} or movement in {
                "horizontal_pull",
                "vertical_pull",
                "elbow_flexion",
                "hinge",
            }
        return True

    def _usage_date(self):
        return datetime.now(timezone.utc).date()

    def _build_ai_request_log(
        self,
        request_id,
        command: GenerateWorkoutCommand,
        status: str,
        input_payload: dict,
        output_payload: dict | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        fallback_used: bool = False,
        latency_ms: int | None = None,
    ) -> AIRequestLog:
        settings = get_settings()
        return AIRequestLog(
            id=request_id,
            user_id=command.user_id,
            workout_plan_id=None,
            request_type="generate_workout",
            provider=settings.AI_PROVIDER,
            model_name=settings.OPENROUTER_MODEL,
            generation_mode=command.generation_mode,
            input_payload=input_payload,
            output_payload=output_payload or {},
            status=status,
            error_code=error_code,
            error_message=error_message,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
        )

    def _to_exercise_dto(self, item, exercise: Exercise | None) -> WorkoutExerciseDTO:
        return WorkoutExerciseDTO(
            workout_plan_exercise_id=item.id,
            exercise_id=item.exercise_id,
            name=(
                (item.name or exercise.name)
                if exercise
                else (item.name or "Unknown Exercise")
            ),
            order_index=item.order_index,
            primary_muscle=(
                (item.primary_muscle or exercise.muscle_group.value)
                if exercise
                else (item.primary_muscle or MuscleGroup.FULL_BODY.value)
            ),
            equipment=(
                (item.equipment or exercise.equipment_type.value)
                if exercise
                else (item.equipment or EquipmentType.BODYWEIGHT.value)
            ),
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
                by_exercise.setdefault(set_log.workout_plan_exercise_id, []).append(
                    set_log
                )
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
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        program_repository: ProgramRepository | None = None,
    ) -> None:
        self.workout_repository = workout_repository
        self.program_repository = program_repository

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
            await self._update_program_instance(plan.id)
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
        await self._update_program_instance(plan.id)
        return StartWorkoutDTO(
            workout_id=plan.id,
            workout_log_id=log.id,
            status=plan.status.value,
            started_at=log.started_at,
        )

    async def _update_program_instance(self, workout_plan_id: UUID) -> None:
        if self.program_repository is None:
            return
        instance = await self.program_repository.get_instance_by_workout_plan_id(
            workout_plan_id
        )
        if instance is not None:
            await self.program_repository.update_instance_status(
                instance.id, ProgramWorkoutStatus.STARTED
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

        log = await self.workout_repository.get_workout_log_by_id(
            command.workout_log_id
        )
        if (
            log is None
            or log.user_id != command.user_id
            or log.workout_plan_id != command.workout_id
        ):
            raise NotFoundError("Workout log not found.")

        plan_exercise = next(
            (
                item
                for item in plan.exercises
                if item.id == command.workout_plan_exercise_id
            ),
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


class SuggestExerciseReplacementUseCase:
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        exercise_repository: ExerciseRepository,
        user_repository: UserRepository,
    ) -> None:
        self.workout_repository = workout_repository
        self.exercise_repository = exercise_repository
        self.user_repository = user_repository

    async def execute(
        self, command: SuggestExerciseReplacementCommand
    ) -> SuggestExerciseReplacementDTO:
        plan = await self.workout_repository.get_plan_detail_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")

        current = next(
            (
                item
                for item in plan.exercises
                if item.id == command.workout_plan_exercise_id
            ),
            None,
        )
        if current is None:
            raise NotFoundError("Workout exercise not found in plan.")

        profile = await self.user_repository.get_profile(command.user_id)
        level = profile.training_level.value if profile is not None else None
        equipment = command.available_equipment or [EquipmentType.BODYWEIGHT.value]
        candidates = await self.exercise_repository.find_replacement_candidates(
            current_exercise_id=current.exercise_id,
            primary_muscle=current.primary_muscle or MuscleGroup.FULL_BODY.value,
            equipment=equipment,
            level=level,
            limit=5,
        )

        return SuggestExerciseReplacementDTO(
            current_exercise=ReplacementCurrentExerciseDTO(
                exercise_id=current.exercise_id,
                name=current.name or "Current exercise",
                primary_muscle=current.primary_muscle or MuscleGroup.FULL_BODY.value,
                equipment=current.equipment or EquipmentType.BODYWEIGHT.value,
            ),
            replacement_options=[
                ReplacementOptionDTO(
                    exercise_id=item.id,
                    name=item.name,
                    primary_muscle=item.muscle_group.value,
                    equipment=item.equipment_type.value,
                    difficulty=item.training_level.value,
                    target_sets=current.target_sets,
                    target_reps=current.target_reps,
                    rest_seconds=current.rest_seconds or 60,
                    target_rpe=current.target_rpe,
                    reason=self._replacement_reason(current, item, command.reason),
                    safety_note=item.safety_notes,
                )
                for item in candidates
            ],
            safety_note="Choose a replacement that feels pain-free and matches your available setup.",
        )

    def _replacement_reason(self, current, replacement: Exercise, reason: str) -> str:
        reason_label = reason.replace("_", " ")
        if current.equipment != replacement.equipment_type.value:
            return (
                f"Matches {current.primary_muscle} while using "
                f"{replacement.equipment_type.value.replace('_', ' ')} for {reason_label}."
            )
        return f"Targets the same muscle group with a similar training demand for {reason_label}."


class ApplyExerciseReplacementUseCase:
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        exercise_repository: ExerciseRepository,
    ) -> None:
        self.workout_repository = workout_repository
        self.exercise_repository = exercise_repository

    async def execute(
        self, command: ApplyExerciseReplacementCommand
    ) -> ApplyExerciseReplacementDTO:
        plan = await self.workout_repository.get_plan_detail_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")

        plan_exercise = next(
            (
                item
                for item in plan.exercises
                if item.id == command.workout_plan_exercise_id
            ),
            None,
        )
        if plan_exercise is None:
            raise NotFoundError("Workout exercise not found in plan.")

        replacement = await self.exercise_repository.get_by_id(
            command.replacement_exercise_id
        )
        if replacement is None:
            raise NotFoundError("Replacement exercise not found.")

        replaced_exercise_id = plan_exercise.exercise_id
        plan_exercise.exercise_id = replacement.id
        plan_exercise.target_sets = command.target_sets
        plan_exercise.target_reps = command.target_reps
        plan_exercise.rest_seconds = command.rest_seconds
        plan_exercise.target_rpe = command.target_rpe or plan_exercise.target_rpe
        plan_exercise.target_weight = None
        plan_exercise.notes = replacement.safety_notes or replacement.instruction
        await self.workout_repository.update_plan_exercise(plan_exercise)

        return ApplyExerciseReplacementDTO(
            workout_id=plan.id,
            workout_plan_exercise_id=plan_exercise.id,
            replaced_exercise_id=replaced_exercise_id,
            replacement_exercise_id=replacement.id,
            name=replacement.name,
            primary_muscle=replacement.muscle_group.value,
            equipment=replacement.equipment_type.value,
            target_sets=plan_exercise.target_sets,
            target_reps=plan_exercise.target_reps,
            rest_seconds=plan_exercise.rest_seconds or 60,
            target_rpe=plan_exercise.target_rpe,
            is_replacement=True,
        )


class CompleteWorkoutUseCase:
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        volume_calculator: WorkoutVolumeCalculator,
        program_repository: ProgramRepository | None = None,
    ) -> None:
        self.workout_repository = workout_repository
        self.volume_calculator = volume_calculator
        self.program_repository = program_repository

    async def execute(self, command: CompleteWorkoutCommand) -> CompleteWorkoutDTO:
        plan = await self.workout_repository.get_plan_by_id(command.workout_id)
        if plan is None or plan.user_id != command.user_id:
            raise NotFoundError("Workout not found.")

        log = await self.workout_repository.get_workout_log_by_id(
            command.workout_log_id
        )
        if (
            log is None
            or log.user_id != command.user_id
            or log.workout_plan_id != command.workout_id
        ):
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
        log.max_heart_rate = command.max_heart_rate
        log.min_heart_rate = command.min_heart_rate
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
        if self.program_repository is not None:
            instance = await self.program_repository.get_instance_by_workout_plan_id(
                plan.id
            )
            if instance is not None:
                await self.program_repository.update_instance_status(
                    instance.id, ProgramWorkoutStatus.COMPLETED
                )

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
