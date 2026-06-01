from src.domain.ai.entities import AIWorkoutGenerationContext, AIWorkoutGenerationResult
from src.domain.common.exceptions import AIExerciseMappingError, AIUnsafeOutputError


class AIWorkoutSafetyValidator:
    def validate(
        self,
        result: AIWorkoutGenerationResult,
        context: AIWorkoutGenerationContext,
    ) -> None:
        allowed_by_slug = {item.slug: item for item in context.allowed_exercises}
        avoid_normalized = {item.strip().lower() for item in context.avoid_exercises if item.strip()}
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
            if exercise.exercise_slug.lower() in avoid_normalized or allowed.name.lower() in avoid_normalized:
                raise AIUnsafeOutputError("AI selected an avoided exercise.")
            if context.training_level == "beginner" and allowed.difficulty == "advanced":
                raise AIUnsafeOutputError("AI selected advanced exercise for beginner.")
            if exercise.sets > 5:
                raise AIUnsafeOutputError("AI sets exceed safety limit.")

        if context.readiness_score < 20:
            if result.training_decision not in {"recovery", "rest_day"}:
                raise AIUnsafeOutputError("Very low readiness only allows recovery or rest_day.")
            if any(item.rpe > 3 for item in result.exercises):
                raise AIUnsafeOutputError("Very low readiness does not allow rpe above 3.")
        elif context.readiness_score < 40:
            if any(item.rpe > 7 for item in result.exercises):
                raise AIUnsafeOutputError("Low readiness does not allow rpe above 7.")
