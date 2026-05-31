from datetime import date, datetime, timezone
from uuid import uuid4

from src.domain.common.enums import MuscleGroup, WorkoutSource, WorkoutStatus
from src.domain.common.exceptions import ValidationError
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.readiness.services import ReadinessCalculator
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise
from src.domain.workout.services import WorkoutSafetyPolicy


def test_readiness_calculator_high_score() -> None:
    calculator = ReadinessCalculator()
    today = date.today()
    now = datetime.now(timezone.utc)
    summary = HealthSummary(
        id=uuid4(),
        user_id=uuid4(),
        date=today,
        sleep_hours=8.2,
        sleep_efficiency=92.0,
        resting_heart_rate=54.0,
        heart_rate_variability=82.0,
        steps=10000,
        active_energy_kcal=600.0,
        created_at=now,
        updated_at=now,
    )
    checkin = ManualCheckin(
        id=uuid4(),
        user_id=summary.user_id,
        date=today,
        energy=5,
        soreness=1,
        stress=1,
        motivation=5,
        sleep_quality=5,
        notes=None,
        created_at=now,
        updated_at=now,
    )

    score, category, recommendation, confidence, explanation = calculator.calculate(
        health_summary=summary,
        manual_checkin=checkin,
    )

    assert score >= 90
    assert category.value == "excellent"
    assert recommendation.value == "train_hard"
    assert confidence >= 0.9
    assert "Readiness" in explanation


def test_workout_safety_policy_blocks_normal_workout_when_readiness_very_low() -> None:
    policy = WorkoutSafetyPolicy()
    plan = WorkoutPlan(
        id=uuid4(),
        user_id=uuid4(),
        title="Push Day",
        focus=MuscleGroup.CHEST,
        status=WorkoutStatus.GENERATED,
        source=WorkoutSource.AI,
        readiness_score=15,
        decision="normal_volume",
        exercises=[
            WorkoutPlanExercise(
                id=uuid4(),
                workout_plan_id=uuid4(),
                exercise_id=uuid4(),
                order_index=1,
                target_sets=4,
                target_reps="8-10",
                target_rpe=8,
                notes=None,
            )
        ],
    )

    try:
        policy.validate(plan, readiness_score=15)
    except ValidationError as exc:
        assert "recovery or rest_day" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for unsafe very-low-readiness workout")
