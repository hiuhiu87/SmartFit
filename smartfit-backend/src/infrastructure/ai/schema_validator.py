from src.domain.ai.entities import (
    AIWorkoutExerciseResult,
    AIWorkoutGenerationResult,
)
from src.domain.common.exceptions import AIInvalidOutputError


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
