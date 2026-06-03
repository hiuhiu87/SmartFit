from src.infrastructure.ai.schema_validator import AIWorkoutSchemaValidator


def test_workout_schema_validator_coerces_common_numeric_formats() -> None:
    validator = AIWorkoutSchemaValidator()

    result = validator.validate_workout_output(
        {
            "workout_title": "Full Body Session",
            "training_decision": "Reduced Volume",
            "estimated_duration_minutes": "45",
            "exercises": [
                {
                    "exercise_slug": "push-up",
                    "sets": "3",
                    "reps": "8-10",
                    "rest_seconds": 10,
                    "rpe": "7",
                    "notes": "Controlled reps.",
                }
            ],
            "reasoning_summary": "Compact full-body session.",
            "safety_note": "Stop if you feel sharp pain.",
        }
    )

    assert result.training_decision == "reduced_volume"
    assert result.estimated_duration_minutes == 45
    assert result.exercises[0].sets == 3
    assert result.exercises[0].rest_seconds == 15
    assert result.exercises[0].rpe == 7


def test_workout_schema_validator_allows_zero_rest_at_schema_level() -> None:
    validator = AIWorkoutSchemaValidator()

    result = validator.validate_workout_output(
        {
            "workout_title": "Recovery Walk",
            "training_decision": "recovery",
            "estimated_duration_minutes": 20,
            "exercises": [
                {
                    "exercise_slug": "treadmill-zone-2-walk",
                    "sets": 1,
                    "reps": "20 minutes",
                    "rest_seconds": 0,
                    "rpe": 4,
                    "notes": "Steady pace.",
                }
            ],
            "reasoning_summary": "Continuous cardio block.",
            "safety_note": "Stop if you feel sharp pain.",
        }
    )

    assert result.exercises[0].rest_seconds == 0
