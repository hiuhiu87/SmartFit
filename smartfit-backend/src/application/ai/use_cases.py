from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)

from src.application.ai.commands import AIChatCommand
from src.application.ai.dto import (
    AIChatHistoryDTO,
    AIChatHistoryItemDTO,
    AIChatResponseDTO,
    AIChatSuggestedActionDTO,
)
from src.application.ai.queries import GetAIChatHistoryQuery
from src.application.ai_usage.commands import (
    CheckAIUsageLimitCommand,
    RecordAIUsageCommand,
)
from src.application.ai_usage.use_cases import AIUsageService
from app.settings import get_settings
from src.domain.ai.entities import AIChatContext, AIChatResult, AIRequestLog
from src.domain.ai.ports import AIRequestRepository, AIWorkoutGeneratorPort
from src.domain.common.enums import AIRequestStatus, AIRequestType, EquipmentType
from src.domain.common.exceptions import (
    AIChatGenerationError,
    AIChatInvalidOutputError,
    AIChatUnsafeOutputError,
    AIConfigurationError,
    AIExerciseMappingError,
    AIGenerationError,
    AIInvalidOutputError,
    AIProviderTimeoutError,
    AIRateLimitError,
    AIUnsafeOutputError,
    AIUsageLimitExceededError,
    NotFoundError,
    ValidationError,
)
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.readiness.entities import ReadinessScore
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.user.repositories import UserRepository
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise, WorkoutSetLog
from src.domain.workout.repositories import WorkoutRepository
from src.infrastructure.database.base import utcnow
from src.infrastructure.ai.safety_validator import AIChatSafetyValidator

PAIN_TERMS = {
    "pain",
    "hurt",
    "hurts",
    "sore",
    "sharp",
    "dizzy",
    "dizziness",
    "lightheaded",
    "numb",
    "tingling",
    "discomfort",
}


class AIChatUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        readiness_repository: ReadinessRepository,
        exercise_repository: ExerciseRepository,
        workout_repository: WorkoutRepository,
        ai_request_repository: AIRequestRepository,
        ai_chat_generator: AIWorkoutGeneratorPort,
        ai_chat_safety_validator: AIChatSafetyValidator,
        ai_usage_service: AIUsageService,
    ) -> None:
        self.user_repository = user_repository
        self.readiness_repository = readiness_repository
        self.exercise_repository = exercise_repository
        self.workout_repository = workout_repository
        self.ai_request_repository = ai_request_repository
        self.ai_chat_generator = ai_chat_generator
        self.ai_chat_safety_validator = ai_chat_safety_validator
        self.ai_usage_service = ai_usage_service

    async def execute(self, command: AIChatCommand) -> AIChatResponseDTO:
        message = command.message.strip()
        if not message:
            raise ValidationError("Message cannot be empty.")
        if len(message) > 1000:
            raise ValidationError("Message is too long.")

        workout = await self.workout_repository.get_plan_detail_by_id(
            command.workout_id
        )
        if workout is None or workout.user_id != command.user_id:
            raise NotFoundError("Workout not found.")

        current_exercise = self._find_current_exercise(
            workout, command.current_workout_plan_exercise_id
        )
        latest_log = await self.workout_repository.get_latest_log_by_plan_id(
            command.user_id, command.workout_id
        )
        set_logs: list[WorkoutSetLog] = []
        if latest_log is not None:
            set_logs = await self.workout_repository.get_set_logs_by_workout_log_id(
                latest_log.id
            )

        profile = await self.user_repository.get_profile(command.user_id)
        equipment = [
            item.equipment_type.value
            for item in await self.user_repository.get_equipment(command.user_id)
        ] or [EquipmentType.BODYWEIGHT.value]
        readiness = await self.readiness_repository.get_by_date(
            command.user_id, workout.target_date
        )
        if readiness is None:
            readiness = await self.readiness_repository.get_latest(command.user_id)

        replacements = await self._build_replacements(
            current_exercise=current_exercise,
            equipment=equipment,
            training_level=profile.training_level.value if profile else None,
        )

        context = self._build_context(
            command=command,
            workout=workout,
            profile=profile,
            readiness=readiness,
            current_exercise=current_exercise,
            replacements=replacements,
            equipment=equipment,
            set_logs=set_logs,
        )

        usage_date = datetime.now(timezone.utc).date()
        request_id = uuid4()
        input_payload = {
            "message": message,
            "workout_id": str(command.workout_id),
            "current_workout_plan_exercise_id": (
                str(command.current_workout_plan_exercise_id)
                if command.current_workout_plan_exercise_id
                else None
            ),
            "readiness_score": (
                context.readiness_summary.get("score")
                if context.readiness_summary
                else None
            ),
            "readiness_category": (
                context.readiness_summary.get("category")
                if context.readiness_summary
                else None
            ),
            "available_replacement_ids": [
                str(item["exercise_id"])
                for item in replacements
                if item.get("exercise_id")
            ],
        }
        try:
            await self.ai_usage_service.check_limit(
                CheckAIUsageLimitCommand(
                    user_id=command.user_id,
                    request_type="chat",
                    target_date=usage_date,
                )
            )
        except AIUsageLimitExceededError as exc:
            await self.ai_usage_service.record_log_only(
                self._build_ai_request_log(
                    request_id=request_id,
                    command=command,
                    status="blocked",
                    input_payload=input_payload,
                    error_code="AI_LIMIT_REACHED",
                    error_message=str(exc),
                    fallback_used=False,
                    latency_ms=0,
                )
            )
            raise

        await self.ai_usage_service.record_log_only(
            self._build_ai_request_log(
                request_id=request_id,
                command=command,
                status="failed",
                input_payload=input_payload,
                fallback_used=False,
                latency_ms=None,
            )
        )
        await self.ai_request_repository.save_chat_message(
            user_id=command.user_id,
            workout_plan_id=command.workout_id,
            workout_plan_exercise_id=command.current_workout_plan_exercise_id,
            role="user",
            message=message,
            ai_request_id=request_id,
        )

        started = perf_counter()
        try:
            result = await self.ai_chat_generator.chat(context)
            self.ai_chat_safety_validator.validate(result, context)
            latency_ms = int((perf_counter() - started) * 1000)
            await self.ai_usage_service.record(
                RecordAIUsageCommand(
                    user_id=command.user_id,
                    request_type="chat",
                    target_date=usage_date,
                    request_log=self._build_ai_request_log(
                        request_id=request_id,
                        command=command,
                        status="success",
                        input_payload=input_payload,
                        output_payload=self._result_payload(result),
                        fallback_used=False,
                        latency_ms=latency_ms,
                    ),
                )
            )
        except (
            AIChatGenerationError,
            AIChatInvalidOutputError,
            AIChatUnsafeOutputError,
            AIConfigurationError,
            AIExerciseMappingError,
            AIGenerationError,
            AIInvalidOutputError,
            AIProviderTimeoutError,
            AIRateLimitError,
            AIUnsafeOutputError,
            Exception,
        ) as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            print(f"\n\n[WARNING] AI CHAT GENERATION FAILED, FALLING BACK TO SAFE RESPONSE. ERROR: {exc}\n\n", flush=True)
            logger.exception(
                "AI chat generation failed, falling back to safe response. Error: %s - %s",
                exc.__class__.__name__,
                exc,
            )
            result = self._build_safe_fallback(message)
            await self.ai_usage_service.record(
                RecordAIUsageCommand(
                    user_id=command.user_id,
                    request_type="chat",
                    target_date=usage_date,
                    request_log=self._build_ai_request_log(
                        request_id=request_id,
                        command=command,
                        status="fallback_used",
                        input_payload=input_payload,
                        output_payload=self._result_payload(result),
                        error_code=exc.__class__.__name__,
                        error_message=str(exc),
                        fallback_used=True,
                        latency_ms=latency_ms,
                    ),
                )
            )

        await self.ai_request_repository.save_chat_message(
            user_id=command.user_id,
            workout_plan_id=command.workout_id,
            workout_plan_exercise_id=command.current_workout_plan_exercise_id,
            role="assistant",
            message=result.reply,
            suggested_action=self._suggested_action_dict(result),
            ai_request_id=request_id,
        )

        return AIChatResponseDTO(
            reply=result.reply,
            intent=result.intent,
            suggested_action=(
                AIChatSuggestedActionDTO(
                    type=result.suggested_action.type,
                    exercise_id=result.suggested_action.exercise_id,
                    exercise_name=result.suggested_action.exercise_name,
                    target_sets=result.suggested_action.target_sets,
                    target_reps=result.suggested_action.target_reps,
                    rest_seconds=result.suggested_action.rest_seconds,
                    target_rpe=result.suggested_action.target_rpe,
                    reason=result.suggested_action.reason,
                )
                if result.suggested_action is not None
                else None
            ),
        )

    async def _build_replacements(
        self,
        current_exercise: WorkoutPlanExercise | None,
        equipment: list[str],
        training_level: str | None,
    ) -> list[dict]:
        if current_exercise is None or current_exercise.primary_muscle is None:
            return []
        candidates = await self.exercise_repository.find_replacement_candidates(
            current_exercise_id=current_exercise.exercise_id,
            primary_muscle=current_exercise.primary_muscle,
            equipment=equipment,
            level=training_level,
            limit=5,
        )
        return [
            {
                "exercise_id": item.id,
                "exercise_name": item.name,
                "slug": item.slug,
                "primary_muscle": item.muscle_group.value,
                "equipment": item.equipment_type.value,
                "difficulty": item.training_level.value,
            }
            for item in candidates
        ]

    def _build_context(
        self,
        command: AIChatCommand,
        workout: WorkoutPlan,
        profile,
        readiness: ReadinessScore | None,
        current_exercise: WorkoutPlanExercise | None,
        replacements: list[dict],
        equipment: list[str],
        set_logs: list[WorkoutSetLog],
    ) -> AIChatContext:
        logs_by_exercise: dict[UUID, list[WorkoutSetLog]] = {}
        for item in set_logs:
            logs_by_exercise.setdefault(item.workout_plan_exercise_id, []).append(item)

        workout_exercises = []
        for item in workout.exercises:
            workout_exercises.append(
                {
                    "workout_plan_exercise_id": item.id,
                    "exercise_id": item.exercise_id,
                    "name": item.name,
                    "primary_muscle": item.primary_muscle,
                    "equipment": item.equipment,
                    "target_sets": item.target_sets,
                    "target_reps": item.target_reps,
                    "target_rpe": item.target_rpe,
                    "rest_seconds": item.rest_seconds,
                    "logged_sets": [
                        {
                            "set_number": log.set_number,
                            "weight": log.weight_kg,
                            "reps": log.reps_completed,
                            "rpe": log.rpe,
                            "completed": log.completed,
                        }
                        for log in logs_by_exercise.get(item.id, [])
                    ],
                }
            )

        current_summary = None
        if current_exercise is not None:
            current_summary = next(
                (
                    item
                    for item in workout_exercises
                    if item["workout_plan_exercise_id"] == current_exercise.id
                ),
                None,
            )

        return AIChatContext(
            user_id=command.user_id,
            workout_id=command.workout_id,
            current_workout_plan_exercise_id=command.current_workout_plan_exercise_id,
            user_message=command.message.strip(),
            user_profile_summary={
                "training_level": (
                    profile.training_level.value if profile else "beginner"
                ),
                "primary_goal": (
                    profile.primary_goal.value if profile else "general_health"
                ),
                "injuries": profile.injuries if profile else [],
                "notes": profile.notes if profile else None,
                "equipment": equipment,
            },
            readiness_summary=(
                {
                    "score": int(round(readiness.score)),
                    "category": readiness.category.value,
                    "recommendation": readiness.recommendation.value,
                    "date": readiness.date.isoformat(),
                }
                if readiness is not None
                else None
            ),
            workout_summary={
                "title": workout.title,
                "status": workout.status.value,
                "source": workout.source.value,
                "target_date": workout.target_date.isoformat(),
                "focus": workout.focus.value,
            },
            current_exercise=current_summary,
            workout_exercises=workout_exercises,
            available_replacements=replacements,
        )

    def _find_current_exercise(
        self,
        workout: WorkoutPlan,
        workout_plan_exercise_id: UUID | None,
    ) -> WorkoutPlanExercise | None:
        if workout_plan_exercise_id is None:
            return None
        for item in workout.exercises:
            if item.id == workout_plan_exercise_id:
                return item
        raise NotFoundError("Workout exercise not found.")

    def _build_safe_fallback(self, message: str) -> AIChatResult:
        lowered = message.lower()
        if any(term in lowered for term in PAIN_TERMS):
            return AIChatResult(
                reply=(
                    "Stop or reduce the exercise if you feel pain, dizziness, or unusual discomfort. "
                    "Use a lighter option, lower effort, or rest before continuing."
                ),
                intent="safety_warning",
                suggested_action=None,
            )
        return AIChatResult(
            reply=(
                "I couldn't generate a detailed answer right now. Please choose a lighter option, "
                "reduce intensity, or take extra rest before continuing."
            ),
            intent="general_workout_question",
            suggested_action=None,
        )

    def _suggested_action_dict(self, result: AIChatResult) -> dict | None:
        if result.suggested_action is None:
            return None
        return {
            "type": result.suggested_action.type,
            "exercise_id": (
                str(result.suggested_action.exercise_id)
                if result.suggested_action.exercise_id
                else None
            ),
            "exercise_name": result.suggested_action.exercise_name,
            "target_sets": result.suggested_action.target_sets,
            "target_reps": result.suggested_action.target_reps,
            "rest_seconds": result.suggested_action.rest_seconds,
            "target_rpe": result.suggested_action.target_rpe,
            "reason": result.suggested_action.reason,
        }

    def _result_payload(self, result: AIChatResult) -> dict:
        return {
            "reply": result.reply,
            "intent": result.intent,
            "suggested_action": self._suggested_action_dict(result),
        }

    def _build_ai_request_log(
        self,
        request_id: UUID,
        command: AIChatCommand,
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
            workout_plan_id=command.workout_id,
            request_type="chat",
            provider=settings.AI_PROVIDER,
            model_name=settings.OPENROUTER_MODEL,
            generation_mode=None,
            input_payload=input_payload,
            output_payload=output_payload or {},
            status=status,
            error_code=error_code,
            error_message=error_message,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            created_at=utcnow(),
        )


class GetAIChatHistoryUseCase:
    def __init__(
        self,
        workout_repository: WorkoutRepository,
        ai_request_repository: AIRequestRepository,
    ) -> None:
        self.workout_repository = workout_repository
        self.ai_request_repository = ai_request_repository

    async def execute(self, query: GetAIChatHistoryQuery) -> AIChatHistoryDTO:
        workout = await self.workout_repository.get_plan_by_id(query.workout_id)
        if workout is None or workout.user_id != query.user_id:
            raise NotFoundError("Workout not found.")

        items, total = await self.ai_request_repository.list_chat_messages_by_workout(
            user_id=query.user_id,
            workout_plan_id=query.workout_id,
            limit=query.limit,
            offset=query.offset,
        )
        return AIChatHistoryDTO(
            items=[
                AIChatHistoryItemDTO(
                    id=item.id,
                    role=item.role,
                    message=item.message,
                    suggested_action=(
                        AIChatSuggestedActionDTO(
                            type=item.suggested_action.get("type", "none"),
                            exercise_id=(
                                UUID(item.suggested_action["exercise_id"])
                                if item.suggested_action.get("exercise_id")
                                else None
                            ),
                            exercise_name=item.suggested_action.get("exercise_name"),
                            target_sets=item.suggested_action.get("target_sets"),
                            target_reps=item.suggested_action.get("target_reps"),
                            rest_seconds=item.suggested_action.get("rest_seconds"),
                            target_rpe=item.suggested_action.get("target_rpe"),
                            reason=item.suggested_action.get("reason"),
                        )
                        if item.suggested_action is not None
                        else None
                    ),
                    workout_plan_exercise_id=item.workout_plan_exercise_id,
                    created_at=item.created_at,
                )
                for item in items
            ],
            limit=query.limit,
            offset=query.offset,
            total=total,
        )
