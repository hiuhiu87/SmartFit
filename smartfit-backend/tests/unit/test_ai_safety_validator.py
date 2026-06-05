from datetime import date
from uuid import uuid4

import pytest

from src.domain.ai.entities import (
    AIAllowedExercise,
    AIWorkoutExerciseResult,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)
from src.domain.common.exceptions import AIUnsafeOutputError
from src.infrastructure.ai.safety_validator import AIWorkoutSafetyValidator


def test_workout_safety_validator_blocks_zero_rest_for_non_continuous_exercise() -> (
    None
):
    validator = AIWorkoutSafetyValidator()
    context = AIWorkoutGenerationContext(
        user_id=uuid4(),
        target_date=date(2026, 6, 1),
        goal="muscle_gain",
        training_level="intermediate",
        readiness_score=60,
        readiness_category="good",
        readiness_recommendation="train_normal",
        focus_muscle="chest",
        available_time_minutes=45,
        equipment=["dumbbell", "bodyweight"],
        allowed_exercises=[
            AIAllowedExercise(
                exercise_id=uuid4(),
                name="Push-up",
                slug="push-up",
                primary_muscle="chest",
                equipment="bodyweight",
                difficulty="beginner",
                movement_type="push",
            )
        ],
    )
    result = AIWorkoutGenerationResult(
        workout_title="Chest Session",
        training_decision="normal_volume",
        estimated_duration_minutes=30,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug="push-up",
                sets=3,
                reps="8-10",
                rest_seconds=0,
                rpe=7,
                notes="Controlled reps.",
            )
        ],
        reasoning_summary="Test payload.",
        safety_note="Stop if you feel sharp pain.",
    )

    with pytest.raises(AIUnsafeOutputError):
        validator.validate(result, context)
