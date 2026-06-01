from uuid import UUID

from src.domain.ai.entities import (
    AIChatResult,
    AIChatSuggestedAction,
    AIWorkoutExerciseResult,
    AIWorkoutGenerationResult,
)
from src.domain.common.exceptions import AIChatInvalidOutputError, AIInvalidOutputError


class AIWorkoutSchemaValidator:
    ALLOWED_DECISIONS = {
        "normal_volume",
        "reduced_volume",
        "recovery",
        "rest_day",
    }

    def validate_workout_output(self, raw: dict) -> AIWorkoutGenerationResult:
        if not isinstance(raw, dict):
            raise AIInvalidOutputError("AI output must be a JSON object.")

        workout_title = raw.get("workout_title")
        training_decision = raw.get("training_decision")
        estimated_duration_minutes = raw.get("estimated_duration_minutes")
        exercises = raw.get("exercises")
        reasoning_summary = raw.get("reasoning_summary")
        safety_note = raw.get("safety_note")

        if not isinstance(workout_title, str) or not workout_title.strip():
            raise AIInvalidOutputError("AI output missing valid workout_title.")
        if training_decision not in self.ALLOWED_DECISIONS:
            raise AIInvalidOutputError("AI output has invalid training_decision.")
        if not isinstance(estimated_duration_minutes, int) or not (
            5 <= estimated_duration_minutes <= 180
        ):
            raise AIInvalidOutputError(
                "AI output has invalid estimated_duration_minutes."
            )
        if not isinstance(exercises, list):
            raise AIInvalidOutputError("AI output exercises must be a list.")
        if not isinstance(reasoning_summary, str) or not reasoning_summary.strip():
            raise AIInvalidOutputError("AI output missing reasoning_summary.")
        if not isinstance(safety_note, str) or not safety_note.strip():
            raise AIInvalidOutputError("AI output missing safety_note.")

        parsed_exercises: list[AIWorkoutExerciseResult] = []
        for item in exercises:
            if not isinstance(item, dict):
                raise AIInvalidOutputError("AI exercise item must be an object.")
            slug = item.get("exercise_slug")
            sets = item.get("sets")
            reps = item.get("reps")
            rest_seconds = item.get("rest_seconds")
            rpe = item.get("rpe")
            notes = item.get("notes")
            if not isinstance(slug, str) or not slug.strip():
                raise AIInvalidOutputError("AI exercise missing exercise_slug.")
            if not isinstance(sets, int) or not (1 <= sets <= 5):
                raise AIInvalidOutputError("AI exercise sets must be 1..5.")
            if not isinstance(reps, str) or not reps.strip():
                raise AIInvalidOutputError("AI exercise missing reps.")
            if not isinstance(rest_seconds, int) or not (15 <= rest_seconds <= 300):
                raise AIInvalidOutputError("AI exercise rest_seconds must be 15..300.")
            if not isinstance(rpe, int) or not (1 <= rpe <= 10):
                raise AIInvalidOutputError("AI exercise rpe must be 1..10.")
            if notes is not None and not isinstance(notes, str):
                raise AIInvalidOutputError("AI exercise notes must be a string.")
            parsed_exercises.append(
                AIWorkoutExerciseResult(
                    exercise_slug=slug,
                    sets=sets,
                    reps=reps,
                    rest_seconds=rest_seconds,
                    rpe=rpe,
                    notes=notes,
                )
            )

        if training_decision != "rest_day" and not parsed_exercises:
            raise AIInvalidOutputError(
                "AI output must include exercises unless training_decision is rest_day."
            )

        return AIWorkoutGenerationResult(
            workout_title=workout_title.strip(),
            training_decision=training_decision,
            estimated_duration_minutes=estimated_duration_minutes,
            exercises=parsed_exercises,
            reasoning_summary=reasoning_summary.strip(),
            safety_note=safety_note.strip(),
        )


class AIChatSchemaValidator:
    ALLOWED_INTENTS = {
        "replace_exercise",
        "reduce_difficulty",
        "explain_exercise",
        "rest_time_advice",
        "general_workout_question",
        "safety_warning",
    }
    ALLOWED_ACTION_TYPES = {
        "replace_exercise",
        "reduce_current_exercise",
        "adjust_rest_time",
        "none",
    }

    def validate(self, raw: dict) -> AIChatResult:
        if not isinstance(raw, dict):
            raise AIChatInvalidOutputError("AI chat output must be a JSON object.")

        reply = raw.get("reply")
        intent = raw.get("intent")
        action_raw = raw.get("suggested_action")

        if not isinstance(reply, str) or not reply.strip():
            raise AIChatInvalidOutputError("AI chat output missing reply.")
        if len(reply) > 600:
            raise AIChatInvalidOutputError("AI chat reply is too long.")
        if intent not in self.ALLOWED_INTENTS:
            raise AIChatInvalidOutputError("AI chat intent is invalid.")

        suggested_action = None
        if action_raw is not None:
            if not isinstance(action_raw, dict):
                raise AIChatInvalidOutputError("AI chat suggested_action must be an object.")
            action_type = action_raw.get("type")
            if action_type not in self.ALLOWED_ACTION_TYPES:
                raise AIChatInvalidOutputError("AI chat action type is invalid.")
            if action_type == "none":
                suggested_action = None
            else:
                exercise_id = action_raw.get("exercise_id")
                exercise_name = action_raw.get("exercise_name")
                target_sets = action_raw.get("target_sets")
                target_reps = action_raw.get("target_reps")
                rest_seconds = action_raw.get("rest_seconds")
                target_rpe = action_raw.get("target_rpe")
                reason = action_raw.get("reason")

                if action_type == "replace_exercise":
                    if not isinstance(exercise_id, str) or not exercise_id.strip():
                        raise AIChatInvalidOutputError(
                            "Replace action requires exercise_id."
                        )
                    if not isinstance(exercise_name, str) or not exercise_name.strip():
                        raise AIChatInvalidOutputError(
                            "Replace action requires exercise_name."
                        )
                if target_sets is not None and (
                    not isinstance(target_sets, int) or not (1 <= target_sets <= 5)
                ):
                    raise AIChatInvalidOutputError("target_sets must be 1..5.")
                if target_reps is not None and (
                    not isinstance(target_reps, str) or not target_reps.strip()
                ):
                    raise AIChatInvalidOutputError("target_reps must be a string.")
                if rest_seconds is not None and (
                    not isinstance(rest_seconds, int) or not (15 <= rest_seconds <= 300)
                ):
                    raise AIChatInvalidOutputError("rest_seconds must be 15..300.")
                if target_rpe is not None and (
                    not isinstance(target_rpe, int) or not (1 <= target_rpe <= 10)
                ):
                    raise AIChatInvalidOutputError("target_rpe must be 1..10.")
                if reason is not None and not isinstance(reason, str):
                    raise AIChatInvalidOutputError("reason must be a string.")

                parsed_exercise_id = None
                if isinstance(exercise_id, str) and exercise_id.strip():
                    try:
                        parsed_exercise_id = UUID(exercise_id)
                    except ValueError as exc:
                        raise AIChatInvalidOutputError(
                            "exercise_id must be a valid UUID."
                        ) from exc
                suggested_action = AIChatSuggestedAction(
                    type=action_type,
                    exercise_id=parsed_exercise_id,
                    exercise_name=exercise_name,
                    target_sets=target_sets,
                    target_reps=target_reps,
                    rest_seconds=rest_seconds,
                    target_rpe=target_rpe,
                    reason=reason,
                )

        if intent == "safety_warning" and suggested_action is not None:
            raise AIChatInvalidOutputError(
                "safety_warning response must not include a suggested action."
            )

        return AIChatResult(
            reply=reply.strip(),
            intent=intent,
            suggested_action=suggested_action,
        )
