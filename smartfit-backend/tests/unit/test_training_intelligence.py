from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.domain.common.enums import (
    EquipmentType,
    Goal,
    MuscleGroup,
    TrainingLevel,
)
from src.domain.exercise.entities import Exercise
from src.domain.health.entities import ManualCheckin
from src.domain.readiness.services import ReadinessCalculator
from src.domain.training.entities import (
    CompletedWorkout,
    SetLogWithExercise,
    TrainingLoadSummary,
    TrainingRecommendationContext,
    WorkoutHealthMetrics,
)
from src.domain.training.services import (
    ExercisePerformanceAnalyzer,
    MuscleFatigueCalculator,
    TrainingLoadCalculator,
    TrainingRecommendationService,
)
from src.domain.workout.services import RuleBasedWorkoutGenerator


class FakeTrainingRepository:
    def __init__(
        self,
        workouts: list[CompletedWorkout] | None = None,
        sets: list[SetLogWithExercise] | None = None,
        metrics: list[WorkoutHealthMetrics] | None = None,
    ) -> None:
        self.workouts = workouts or []
        self.sets = sets or []
        self.metrics = metrics or []

    async def get_completed_workouts(self, user_id, from_date, to_date):
        return self.workouts

    async def get_set_logs_with_exercise(self, user_id, from_date, to_date):
        return self.sets

    async def get_workout_health_metrics(self, user_id, from_date, to_date):
        return self.metrics

    async def get_exercise_history(self, user_id, exercise_id, limit):
        return [item for item in self.sets if item.exercise_id == exercise_id][:limit]


def set_log(
    *,
    exercise_id=None,
    name: str = "Bent Over Row",
    muscle: str = "back",
    completed_at: datetime,
    reps: int = 10,
    weight: float = 70,
    rpe: int = 8,
) -> SetLogWithExercise:
    return SetLogWithExercise(
        workout_log_id=uuid4(),
        workout_plan_exercise_id=uuid4(),
        exercise_id=exercise_id or uuid4(),
        exercise_name=name,
        primary_muscle=muscle,
        secondary_muscles=[],
        completed_at=completed_at,
        set_number=1,
        reps_completed=reps,
        weight_kg=weight,
        rpe=rpe,
        completed=True,
    )


def exercise(name: str, muscle_group: MuscleGroup, movement: str) -> Exercise:
    return Exercise(
        id=uuid4(),
        slug=name.lower().replace(" ", "-"),
        name=name,
        muscle_group=muscle_group,
        equipment_type=EquipmentType.DUMBBELL,
        training_level=TrainingLevel.BEGINNER,
        movement_type=movement,
        movement_pattern=movement,
        exercise_role="main_compound",
        is_active=True,
    )


def generator_exercises() -> list[Exercise]:
    return [
        exercise("Dumbbell Bench Press", MuscleGroup.CHEST, "horizontal_push"),
        exercise("Dumbbell Shoulder Press", MuscleGroup.SHOULDERS, "vertical_push"),
        exercise("Dumbbell Row", MuscleGroup.BACK, "horizontal_pull"),
        exercise("Lat Pulldown", MuscleGroup.BACK, "vertical_pull"),
        exercise("Goblet Squat", MuscleGroup.LEGS, "squat"),
        exercise("Romanian Deadlift", MuscleGroup.LEGS, "hinge"),
        exercise("Dumbbell Curl", MuscleGroup.ARMS, "elbow_flexion"),
        exercise("Bike HIIT Intervals", MuscleGroup.CARDIO, "cardio"),
    ]


@pytest.mark.asyncio
async def test_high_back_volume_yesterday_marks_back_fatigue_high() -> None:
    user_id = uuid4()
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    sets = [
        set_log(completed_at=yesterday, muscle="back", weight=80, reps=10)
        for _ in range(12)
    ]
    calculator = MuscleFatigueCalculator(FakeTrainingRepository(sets=sets))

    fatigue = await calculator.calculate_muscle_fatigue(user_id, to_date=date.today())

    back = next(item for item in fatigue if item.muscle == "back")
    assert back.fatigue_score >= 75
    assert back.recovery_status == "high_fatigue"


def test_high_recent_load_disables_hiit() -> None:
    context = TrainingRecommendationContext(
        recent_load=TrainingLoadSummary(
            user_id=uuid4(),
            from_date=date.today(),
            to_date=date.today(),
            total_volume=20000,
            total_sets=60,
            workout_count=5,
            total_duration_minutes=400,
            avg_rpe=8,
            active_energy_burned=3000,
            avg_heart_rate=145,
            load_score=85,
            load_level="very_high",
        ),
        suggested_focus="upper_body_pull",
        reason="Recent training load is very high.",
    )

    plan = RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=Goal.MUSCLE_GAIN.value,
        training_level=TrainingLevel.BEGINNER.value,
        readiness_score=90,
        readiness_recommendation="train_normal",
        workout_split="pull",
        focus_muscle=None,
        available_time_minutes=60,
        exercises=generator_exercises(),
        avoid_exercises=[],
        available_equipment=["dumbbell", "bodyweight", "bike"],
        training_context=context,
    )

    assert all(item.target_reps != "30s fast / 60s easy" for item in plan.exercises)


def test_no_sleep_data_still_calculates_readiness_from_training_load() -> None:
    checkin = ManualCheckin(
        id=uuid4(),
        user_id=uuid4(),
        date=date.today(),
        energy=4,
        soreness=2,
        stress=2,
        motivation=4,
        sleep_quality=3,
    )

    (
        score,
        category,
        recommendation,
        confidence,
        explanation,
    ) = ReadinessCalculator().calculate(
        health_summary=None,
        manual_checkin=checkin,
        recent_load_score=82,
    )

    assert score >= 70
    assert category.value in {"good", "moderate"}
    assert recommendation.value in {"train_normal", "reduce_volume"}
    assert confidence >= 0.5
    assert "load=82" in explanation


@pytest.mark.asyncio
async def test_suggested_focus_avoids_high_fatigue_muscle() -> None:
    user_id = uuid4()
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    sets = [
        set_log(completed_at=yesterday, muscle="back", weight=80, reps=10)
        for _ in range(12)
    ]
    service = TrainingRecommendationService(
        TrainingLoadCalculator(FakeTrainingRepository(sets=sets)),
        MuscleFatigueCalculator(FakeTrainingRepository(sets=sets)),
    )

    context = await service.build_context(user_id, date.today())

    assert "upper_body_pull" in context.avoid_focus
    assert context.suggested_focus != "upper_body_pull"


def test_exercise_trend_improving_suggests_overload() -> None:
    exercise_id = uuid4()
    now = datetime.now(timezone.utc)
    history = [
        set_log(
            exercise_id=exercise_id,
            completed_at=now - timedelta(days=6),
            weight=50,
            reps=8,
        ),
        set_log(
            exercise_id=exercise_id,
            completed_at=now - timedelta(days=5),
            weight=50,
            reps=8,
        ),
        set_log(
            exercise_id=exercise_id,
            completed_at=now - timedelta(days=4),
            weight=50,
            reps=9,
        ),
        set_log(
            exercise_id=exercise_id,
            completed_at=now - timedelta(days=2),
            weight=50,
            reps=11,
        ),
        set_log(
            exercise_id=exercise_id,
            completed_at=now - timedelta(days=1),
            weight=50,
            reps=12,
        ),
        set_log(exercise_id=exercise_id, completed_at=now, weight=50, reps=12),
    ]

    trend = ExercisePerformanceAnalyzer().analyze(history)

    assert trend is not None
    assert trend.trend == "improving"
    assert trend.suggested_next_weight == 52.5


def test_rule_based_generator_uses_training_context_when_focus_nil() -> None:
    context = TrainingRecommendationContext(
        recent_load=TrainingLoadSummary(
            user_id=uuid4(),
            from_date=date.today(),
            to_date=date.today(),
            total_volume=0,
            total_sets=0,
            workout_count=0,
            total_duration_minutes=0,
            avg_rpe=None,
            active_energy_burned=None,
            avg_heart_rate=None,
            load_score=20,
            load_level="low",
        ),
        suggested_focus="lower_body",
        reason="Lower body is best recovered.",
    )

    plan = RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=Goal.MUSCLE_GAIN.value,
        training_level=TrainingLevel.BEGINNER.value,
        readiness_score=75,
        readiness_recommendation="train_normal",
        workout_split="upper_body",
        focus_muscle=None,
        available_time_minutes=60,
        exercises=generator_exercises(),
        avoid_exercises=[],
        available_equipment=["dumbbell", "bodyweight"],
        training_context=context,
    )

    assert plan.focus.value == "lower_body"
    assert "Training context" in (plan.ai_reasoning_summary or "")
