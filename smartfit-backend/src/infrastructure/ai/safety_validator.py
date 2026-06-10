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
from src.domain.exercise.equipment_policy import get_equipment_category


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
        exercise_count = len(result.exercises)
        if not (
            context.target_exercise_count_min
            <= exercise_count
            <= context.target_exercise_count_max
        ):
            if not (context.readiness_score < 20 and exercise_count <= 3):
                raise AIUnsafeOutputError(
                    "AI workout exercise count is outside the policy target."
                )

        selected_allowed = []
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
            if self._conflicts_with_limitations(allowed, context):
                raise AIUnsafeOutputError(
                    f"AI selected an exercise conflicting with limitations: {allowed.slug}"
                )
            selected_allowed.append(allowed)

        selected_patterns = {
            (item.movement_pattern or item.movement_type or "").strip().lower()
            for item in selected_allowed
        }
        missing_patterns = (
            set(context.movement_pattern_requirements) - selected_patterns
        )
        if missing_patterns:
            raise AIUnsafeOutputError(
                f"AI workout is missing required movement patterns: {sorted(missing_patterns)}"
            )

        self._validate_equipment_mix(selected_allowed, context)
        self._validate_order(selected_allowed)
        self._validate_progression(result, context)

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
        if context.training_style == "returning" and any(
            item.rpe > 7 for item in result.exercises
        ):
            raise AIUnsafeOutputError("Returning training style caps rpe at 7.")

    def _allows_zero_rest(self, allowed) -> bool:
        movement_type = (allowed.movement_type or "").strip().lower()
        primary_muscle = (allowed.primary_muscle or "").strip().lower()
        return (
            movement_type in self.ZERO_REST_MOVEMENTS
            or primary_muscle in self.ZERO_REST_MUSCLES
        )

    def _validate_equipment_mix(
        self, selected: list, context: AIWorkoutGenerationContext
    ) -> None:
        available_categories = {
            get_equipment_category(item.equipment) for item in context.allowed_exercises
        } - {"other"}
        if len(available_categories) < 3 or not selected:
            return
        categories = [get_equipment_category(item.equipment) for item in selected]
        largest = max(categories.count(category) for category in set(categories))
        if largest / len(categories) > 0.6:
            raise AIUnsafeOutputError(
                "AI workout overuses one equipment category despite alternatives."
            )

    def _validate_order(self, selected: list) -> None:
        buckets = [self._order_bucket(item) for item in selected]
        if buckets != sorted(buckets):
            raise AIUnsafeOutputError("AI workout violates exercise ordering policy.")

    def _order_bucket(self, exercise) -> int:
        pattern = (
            (exercise.movement_pattern or exercise.movement_type or "").strip().lower()
        )
        role = (exercise.exercise_role or "").strip().lower()
        name = exercise.name.lower()
        if pattern == "mobility" and (
            "stretch" in name or "cooldown" in name or role == "cooldown_mobility"
        ):
            return 9
        if pattern == "cardio":
            return 8
        if pattern == "core" or role == "core":
            return 7
        if role == "corrective":
            return 6
        if role == "isolation":
            return 5
        if role == "accessory":
            return 4
        if role in {"secondary", "secondary_compound"}:
            return 3
        if role in {"primary", "primary_compound", "main_compound"}:
            return 2
        if pattern == "mobility" or role in {"warmup", "activation"}:
            return 1
        return 4

    def _validate_progression(
        self,
        result: AIWorkoutGenerationResult,
        context: AIWorkoutGenerationContext,
    ) -> None:
        progression = {item.exercise_slug: item for item in context.progression_context}
        for exercise in result.exercises:
            constraint = progression.get(exercise.exercise_slug)
            if constraint is None:
                continue
            if constraint.progression_action in {"reduce_volume", "deload"}:
                if exercise.sets > 3 or exercise.rpe > 7:
                    raise AIUnsafeOutputError(
                        "AI ignored a reduce-volume progression constraint."
                    )
            if constraint.progression_action == "reduce_weight" and exercise.rpe > 8:
                raise AIUnsafeOutputError(
                    "AI ignored a reduce-weight progression constraint."
                )
            if (
                constraint.suggested_weight is not None
                and exercise.target_weight is not None
                and exercise.target_weight > constraint.suggested_weight * 1.1
            ):
                raise AIUnsafeOutputError(
                    "AI exceeded the progression weight recommendation."
                )

    def _conflicts_with_limitations(
        self, exercise, context: AIWorkoutGenerationContext
    ) -> bool:
        limitations = " ".join(
            item.lower()
            for item in [
                *context.injuries,
                *context.movement_limitations,
                *context.pain_areas,
                *context.pain_movements,
            ]
        )
        pattern = (
            (exercise.movement_pattern or exercise.movement_type or "").strip().lower()
        )
        name = exercise.name.lower()
        if any(term in limitations for term in {"lower_back", "lower back", "spine"}):
            if pattern == "horizontal_pull" and any(
                term in name for term in {"bent over", "bent-over", "unsupported"}
            ):
                return True
        if any(term in limitations for term in {"overhead", "shoulder_overhead"}):
            if pattern == "vertical_push" or "overhead press" in name:
                return True
        if "knee" in limitations and pattern in {"squat", "lunge"}:
            return True
        return False


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
