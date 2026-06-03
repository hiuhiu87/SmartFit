from uuid import UUID

from src.domain.ai.entities import (
    AIChatContext,
    AIChatResult,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)
from src.domain.common.exceptions import (
    AIChatUnsafeOutputError,
    AIExerciseMappingError,
    AIUnsafeOutputError,
)


class AIWorkoutSafetyValidator:
    ZERO_REST_MOVEMENTS = {"cardio", "mobility"}
    ZERO_REST_MUSCLES = {"cardio", "mobility"}

    def validate(
        self,
        result: AIWorkoutGenerationResult,
        context: AIWorkoutGenerationContext,
    ) -> None:
        allowed_by_slug = {item.slug: item for item in context.allowed_exercises}
        avoid_normalized = {
            item.strip().lower() for item in context.avoid_exercises if item.strip()
        }
        available_equipment = set(context.equipment) | {"bodyweight"}

        if result.estimated_duration_minutes > context.available_time_minutes + 10:
            raise AIUnsafeOutputError("AI workout exceeds allowed duration window.")

        for exercise in result.exercises:
            allowed = allowed_by_slug.get(exercise.exercise_slug)
            if allowed is None:
                raise AIExerciseMappingError(
                    f"Unknown exercise slug from AI: {exercise.exercise_slug}"
                )
            if allowed.equipment not in available_equipment:
                raise AIUnsafeOutputError(
                    f"AI selected unsupported equipment: {allowed.equipment}"
                )
            if (
                exercise.exercise_slug.lower() in avoid_normalized
                or allowed.name.lower() in avoid_normalized
            ):
                raise AIUnsafeOutputError("AI selected an avoided exercise.")
            if (
                context.training_level == "beginner"
                and allowed.difficulty == "advanced"
            ):
                raise AIUnsafeOutputError("AI selected advanced exercise for beginner.")
            if exercise.sets > 5:
                raise AIUnsafeOutputError("AI sets exceed safety limit.")
            if exercise.rest_seconds == 0 and not self._allows_zero_rest(allowed):
                raise AIUnsafeOutputError(
                    f"AI selected rest_seconds=0 for non-continuous exercise: {exercise.exercise_slug}"
                )

        if context.readiness_score < 20:
            if result.training_decision not in {"recovery", "rest_day"}:
                raise AIUnsafeOutputError(
                    "Very low readiness only allows recovery or rest_day."
                )
            if any(item.rpe > 3 for item in result.exercises):
                raise AIUnsafeOutputError(
                    "Very low readiness does not allow rpe above 3."
                )
        elif context.readiness_score < 40:
            if any(item.rpe > 7 for item in result.exercises):
                raise AIUnsafeOutputError("Low readiness does not allow rpe above 7.")

    def _allows_zero_rest(self, allowed) -> bool:
        movement_type = (allowed.movement_type or "").strip().lower()
        primary_muscle = (allowed.primary_muscle or "").strip().lower()
        return (
            movement_type in self.ZERO_REST_MOVEMENTS
            or primary_muscle in self.ZERO_REST_MUSCLES
        )


class AIChatSafetyValidator:
    PAIN_TERMS = {
        "pain",
        "hurt",
        "hurts",
        "sharp",
        "dizzy",
        "dizziness",
        "lightheaded",
        "discomfort",
    }
    MEDICAL_TERMS = {
        "diagnose",
        "diagnosis",
        "tear",
        "fracture",
        "dislocation",
        "tendonitis",
    }
    IGNORE_PAIN_TERMS = {
        "push through the pain",
        "ignore the pain",
        "keep going through pain",
    }
    MODIFIED_WORKOUT_TERMS = {
        "i replaced",
        "i changed your workout",
        "i updated your workout",
    }

    def validate(self, result: AIChatResult, context: AIChatContext) -> None:
        reply_lower = result.reply.lower()
        message_lower = context.user_message.lower()

        if any(term in reply_lower for term in self.MEDICAL_TERMS):
            raise AIChatUnsafeOutputError(
                "AI chat response contains medical diagnosis language."
            )
        if any(term in reply_lower for term in self.IGNORE_PAIN_TERMS):
            raise AIChatUnsafeOutputError(
                "AI chat response tells the user to ignore pain."
            )
        if any(term in reply_lower for term in self.MODIFIED_WORKOUT_TERMS):
            raise AIChatUnsafeOutputError(
                "AI chat response incorrectly claims the workout was already changed."
            )
        if any(
            term in message_lower for term in self.PAIN_TERMS
        ) and result.intent not in {
            "safety_warning",
            "reduce_difficulty",
        }:
            raise AIChatUnsafeOutputError(
                "Pain-related user message requires a safety-focused response."
            )

        if result.suggested_action is None:
            return

        if result.suggested_action.type == "replace_exercise":
            replacement_ids = {
                str(item.get("exercise_id"))
                for item in context.available_replacements
                if item.get("exercise_id") is not None
            }
            if str(result.suggested_action.exercise_id) not in replacement_ids:
                raise AIChatUnsafeOutputError(
                    "AI chat replacement exercise is not in allowed replacements."
                )

        readiness_score = None
        if context.readiness_summary is not None:
            readiness_score = context.readiness_summary.get("score")
        if readiness_score is not None and readiness_score < 40:
            target_rpe = result.suggested_action.target_rpe
            if target_rpe is not None and target_rpe > 7:
                raise AIChatUnsafeOutputError(
                    "Low readiness does not allow target_rpe above 7."
                )
