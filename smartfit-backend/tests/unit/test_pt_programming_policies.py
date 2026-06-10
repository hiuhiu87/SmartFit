from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.application.workout.use_cases import GenerateWorkoutUseCase
from src.domain.ai.entities import (
    AIAllowedExercise,
    AIWorkoutExerciseResult,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)
from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel
from src.domain.common.exceptions import AIUnsafeOutputError
from src.domain.exercise.entities import Exercise
from src.domain.program.split_selection_policy import SplitSelectionPolicy
from src.domain.progression.entities import (
    ExercisePerformanceHistory,
    ExerciseSessionPerformance,
    SetPerformance,
)
from src.domain.workout.equipment_diversity_policy import EquipmentDiversityPolicy
from src.domain.workout.services import RuleBasedWorkoutGenerator
from src.domain.workout.workout_ordering_policy import WorkoutOrderingPolicy
from src.domain.workout.workout_volume_policy import WorkoutVolumePolicy
from src.infrastructure.ai.safety_validator import AIWorkoutSafetyValidator


def _exercise(
    name: str,
    equipment: EquipmentType,
    pattern: str,
    role: str,
    muscle: MuscleGroup = MuscleGroup.BACK,
) -> Exercise:
    return Exercise(
        id=uuid4(),
        slug=name.lower().replace(" ", "-"),
        name=name,
        muscle_group=muscle,
        equipment_type=equipment,
        training_level=TrainingLevel.BEGINNER,
        movement_type=pattern,
        movement_pattern=pattern,
        exercise_role=role,
        joint_stress="low",
        substitution_group=name.lower(),
    )


def test_workout_volume_policy_beginner_60_min_returns_around_5() -> None:
    assert WorkoutVolumePolicy().target_exercise_count(
        "beginner", 60, "balanced", 75
    ) == (5, 5)


def test_workout_volume_policy_intermediate_60_min_returns_5_to_7() -> None:
    assert WorkoutVolumePolicy().target_exercise_count(
        "intermediate", 60, "balanced", 75
    ) == (5, 7)


def test_workout_volume_policy_caps_large_muscle_sets() -> None:
    policy = WorkoutVolumePolicy()
    assert policy.max_quality_sets_per_muscle("beginner", "large", 80) == 5
    assert policy.max_quality_sets_per_muscle("advanced", "large", 80) == 8
    assert policy.max_quality_sets_per_muscle("advanced", "large", 30) < 8


def test_equipment_diversity_prevents_all_bodyweight_when_gym_available() -> None:
    policy = EquipmentDiversityPolicy()
    selected = [
        _exercise(
            f"Push Up {index}", EquipmentType.BODYWEIGHT, "horizontal_push", "accessory"
        )
        for index in range(5)
    ]
    candidates = [
        [
            selected[index],
            _exercise(
                f"Dumbbell {index}",
                EquipmentType.DUMBBELL,
                "horizontal_push",
                "accessory",
            ),
        ]
        for index in range(5)
    ]
    resolved = policy.resolve_diversity_if_needed(
        selected,
        candidates,
        {
            "available_equipment": ["bodyweight", "dumbbell", "machine"],
            "workout_type": "balanced",
        },
    )
    assert len({item.equipment_type for item in resolved}) > 1


def test_equipment_diversity_prevents_all_machine_when_free_weights_available() -> None:
    policy = EquipmentDiversityPolicy()
    selected = [
        _exercise(
            f"Machine {index}", EquipmentType.MACHINE, "horizontal_pull", "accessory"
        )
        for index in range(5)
    ]
    candidates = [
        [
            selected[index],
            _exercise(
                f"Dumbbell Row {index}",
                EquipmentType.DUMBBELL,
                "horizontal_pull",
                "accessory",
            ),
        ]
        for index in range(5)
    ]
    resolved = policy.resolve_diversity_if_needed(
        selected,
        candidates,
        {
            "available_equipment": ["machine", "dumbbell", "bodyweight"],
            "workout_type": "balanced",
        },
    )
    assert any(item.equipment_type == EquipmentType.DUMBBELL for item in resolved)


def test_workout_ordering_places_cooldown_last_and_cardio_before_it() -> None:
    policy = WorkoutOrderingPolicy()
    cooldown = SimpleNamespace(
        name="Cooldown Stretch",
        movement_pattern="mobility",
        exercise_role="corrective",
        rest_seconds=0,
    )
    cardio = SimpleNamespace(
        name="Bike Finisher",
        movement_pattern="cardio",
        exercise_role="finisher",
        rest_seconds=0,
    )
    compound = SimpleNamespace(
        name="Goblet Squat",
        movement_pattern="squat",
        exercise_role="main_compound",
        rest_seconds=90,
    )
    ordered = policy.sort_exercises([cooldown, cardio, compound])
    assert ordered[-1] is cooldown
    assert ordered[-2] is cardio


def test_split_selection_supports_6_days() -> None:
    assert len(SplitSelectionPolicy().get_split_structure(6)) == 6


def test_returning_style_6_days_includes_recovery_or_light_day() -> None:
    titles = [
        item[0].lower()
        for item in SplitSelectionPolicy().get_split_structure(6, "returning")
    ]
    assert any("recovery" in title or "light" in title for title in titles)


def test_lower_back_limitation_prefers_supported_row_over_bent_over_row() -> None:
    generator = RuleBasedWorkoutGenerator()
    bent = _exercise(
        "Bent Over Row", EquipmentType.DUMBBELL, "horizontal_pull", "main_compound"
    )
    supported = _exercise(
        "Chest Supported Row",
        EquipmentType.DUMBBELL,
        "horizontal_pull",
        "secondary_compound",
    )
    assert generator._excluded_by_profile(
        bent,
        "muscle_gain",
        "intermediate",
        [],
        movement_limitations=["lower_back_sensitive"],
    )
    assert not generator._excluded_by_profile(
        supported,
        "muscle_gain",
        "intermediate",
        [],
        movement_limitations=["lower_back_sensitive"],
    )


def test_ai_context_includes_progression_history() -> None:
    exercise = _exercise(
        "Dumbbell Row", EquipmentType.DUMBBELL, "horizontal_pull", "main_compound"
    )
    history = ExercisePerformanceHistory(
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        equipment_type="dumbbell",
        recent_sessions=[
            ExerciseSessionPerformance(
                workout_log_id=uuid4(),
                completed_at=datetime.now(timezone.utc),
                sets=[SetPerformance(weight=20, reps=12, rpe=7, completed=True)] * 3,
            )
        ],
    )
    use_case = GenerateWorkoutUseCase(
        None,
        None,
        None,
        None,
        RuleBasedWorkoutGenerator(),
        None,
        None,
        None,
        None,
        None,
    )
    context = use_case._progression_context(
        [exercise], {exercise.id: history}, "intermediate", 75
    )
    assert context
    assert context[0].exercise_slug == exercise.slug
    assert context[0].last_performance


def test_fitness_assessment_derives_posture_and_returning_styles() -> None:
    use_case = GenerateWorkoutUseCase(
        None,
        None,
        None,
        None,
        RuleBasedWorkoutGenerator(),
        None,
        None,
        None,
        None,
        None,
    )
    sedentary = SimpleNamespace(
        training_history=None,
        months_inactive=None,
        lifestyle_type="sedentary",
        sitting_hours_per_day=9,
    )
    returning = SimpleNamespace(
        training_history="returning_after_break",
        months_inactive=4,
        lifestyle_type=None,
        sitting_hours_per_day=None,
    )
    assert (
        use_case._effective_training_style(
            sedentary, "balanced", has_explicit_override=False
        )
        == "posture"
    )
    assert (
        use_case._effective_training_style(
            returning, "balanced", has_explicit_override=False
        )
        == "returning"
    )


def test_ai_shortlist_covers_push_patterns_and_equipment_categories() -> None:
    use_case = GenerateWorkoutUseCase(
        None,
        None,
        None,
        None,
        RuleBasedWorkoutGenerator(),
        None,
        None,
        None,
        None,
        None,
    )
    arm_fillers = [
        _exercise(
            f"Arm Isolation {index}",
            EquipmentType.BODYWEIGHT,
            "elbow_extension",
            "isolation",
            MuscleGroup.ARMS,
        )
        for index in range(20)
    ]
    candidates = arm_fillers + [
        _exercise(
            "Dumbbell Bench Press",
            EquipmentType.DUMBBELL,
            "horizontal_push",
            "main_compound",
            MuscleGroup.CHEST,
        ),
        _exercise(
            "Machine Chest Press",
            EquipmentType.MACHINE,
            "horizontal_push",
            "secondary_compound",
            MuscleGroup.CHEST,
        ),
        _exercise(
            "Push Up",
            EquipmentType.BODYWEIGHT,
            "horizontal_push",
            "secondary_compound",
            MuscleGroup.CHEST,
        ),
        _exercise(
            "Dumbbell Shoulder Press",
            EquipmentType.DUMBBELL,
            "vertical_push",
            "main_compound",
            MuscleGroup.SHOULDERS,
        ),
        _exercise(
            "Machine Shoulder Press",
            EquipmentType.MACHINE,
            "vertical_push",
            "secondary_compound",
            MuscleGroup.SHOULDERS,
        ),
        _exercise(
            "Cable Triceps Pressdown",
            EquipmentType.CABLE_MACHINE,
            "elbow_extension",
            "isolation",
            MuscleGroup.ARMS,
        ),
    ]

    shortlisted = use_case._select_ai_allowed_exercises(
        candidates,
        focus_muscle="upper_push_balanced",
        workout_split="push",
        avoid_exercises=[],
    )

    patterns = {item.movement_pattern for item in shortlisted}
    categories = {
        EquipmentDiversityPolicy().get_equipment_category(item.equipment_type.value)
        for item in shortlisted
    }
    assert {"horizontal_push", "vertical_push"} <= patterns
    assert {"free_weight", "machine", "bodyweight", "cable"} <= categories
    assert len(shortlisted) == 16


def test_ai_safety_rejects_missing_required_movement_patterns() -> None:
    allowed = AIAllowedExercise(
        exercise_id=uuid4(),
        name="Push Up",
        slug="push-up",
        primary_muscle="chest",
        equipment="bodyweight",
        difficulty="beginner",
        movement_pattern="horizontal_push",
        exercise_role="main_compound",
    )
    context = AIWorkoutGenerationContext(
        user_id=uuid4(),
        target_date=date.today(),
        goal="muscle_gain",
        training_level="intermediate",
        readiness_score=70,
        readiness_category="good",
        readiness_recommendation="train_normal",
        focus_muscle="full_body",
        available_time_minutes=60,
        equipment=["bodyweight"],
        allowed_exercises=[allowed],
        movement_pattern_requirements=["horizontal_push", "horizontal_pull"],
        target_exercise_count_min=1,
        target_exercise_count_max=3,
    )
    result = AIWorkoutGenerationResult(
        workout_title="Test",
        training_decision="normal_volume",
        estimated_duration_minutes=30,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug="push-up",
                sets=3,
                reps="8-12",
                rest_seconds=60,
                rpe=7,
            )
        ],
        reasoning_summary="Test",
        safety_note="Stop for pain.",
    )
    with pytest.raises(AIUnsafeOutputError):
        AIWorkoutSafetyValidator().validate(result, context)
