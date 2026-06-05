from uuid import NAMESPACE_DNS, uuid4, uuid5

from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel
from src.domain.exercise.entities import Exercise
from src.domain.exercise.equipment_policy import get_equipment_category
from src.domain.workout.services import RuleBasedWorkoutGenerator


def _exercise(
    name: str,
    muscle: MuscleGroup,
    equipment: EquipmentType,
    pattern: str,
    role: str,
    group: str,
    *,
    level: TrainingLevel = TrainingLevel.BEGINNER,
    joint_stress: str = "low",
) -> Exercise:
    return Exercise(
        id=uuid5(NAMESPACE_DNS, f"diversity-{name}"),
        slug=name.lower().replace(" ", "-"),
        name=name,
        muscle_group=muscle,
        equipment_type=equipment,
        training_level=level,
        movement_type=pattern,
        movement_pattern=pattern,
        exercise_role=role,
        fatigue_level="medium",
        joint_stress=joint_stress,
        substitution_group=group,
    )


def _catalog() -> list[Exercise]:
    return [
        _exercise(
            "Incline Dumbbell Press",
            MuscleGroup.CHEST,
            EquipmentType.DUMBBELL,
            "horizontal_push",
            "main_compound",
            "incline_press",
        ),
        _exercise(
            "Machine Chest Press",
            MuscleGroup.CHEST,
            EquipmentType.MACHINE,
            "horizontal_push",
            "secondary_compound",
            "chest_press",
        ),
        _exercise(
            "Push Up",
            MuscleGroup.CHEST,
            EquipmentType.BODYWEIGHT,
            "horizontal_push",
            "secondary_compound",
            "push_up",
        ),
        _exercise(
            "Dumbbell Shoulder Press",
            MuscleGroup.SHOULDERS,
            EquipmentType.DUMBBELL,
            "vertical_push",
            "main_compound",
            "shoulder_press",
        ),
        _exercise(
            "Cable Lat Pulldown",
            MuscleGroup.BACK,
            EquipmentType.CABLE_MACHINE,
            "vertical_pull",
            "secondary_compound",
            "vertical_pull",
        ),
        _exercise(
            "Dumbbell Lateral Raise",
            MuscleGroup.SHOULDERS,
            EquipmentType.DUMBBELL,
            "rear_delt",
            "isolation",
            "lateral_raise",
        ),
        _exercise(
            "Cable Face Pull",
            MuscleGroup.SHOULDERS,
            EquipmentType.CABLE_MACHINE,
            "rear_delt",
            "corrective",
            "rear_delt",
        ),
        _exercise(
            "Cable Triceps Pressdown",
            MuscleGroup.ARMS,
            EquipmentType.CABLE_MACHINE,
            "elbow_extension",
            "isolation",
            "triceps",
        ),
        _exercise(
            "Dumbbell Goblet Squat",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            "squat",
            "main_compound",
            "squat",
        ),
        _exercise(
            "Dumbbell Romanian Deadlift",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            "hinge",
            "main_compound",
            "hinge",
        ),
        _exercise(
            "Leg Press",
            MuscleGroup.LEGS,
            EquipmentType.LEG_PRESS,
            "squat",
            "secondary_compound",
            "leg_press",
        ),
        _exercise(
            "Machine Calf Raise",
            MuscleGroup.LEGS,
            EquipmentType.MACHINE,
            "calf_raise",
            "isolation",
            "calf_raise",
        ),
        _exercise(
            "Dumbbell Reverse Lunge",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            "lunge",
            "secondary_compound",
            "lunge",
        ),
        _exercise(
            "Dumbbell Row",
            MuscleGroup.BACK,
            EquipmentType.DUMBBELL,
            "horizontal_pull",
            "main_compound",
            "free_row",
        ),
        _exercise(
            "Machine Supported Row",
            MuscleGroup.BACK,
            EquipmentType.MACHINE,
            "horizontal_pull",
            "secondary_compound",
            "supported_row",
        ),
        _exercise(
            "Dumbbell Curl",
            MuscleGroup.ARMS,
            EquipmentType.DUMBBELL,
            "elbow_flexion",
            "isolation",
            "biceps",
        ),
        _exercise(
            "Plank",
            MuscleGroup.CORE,
            EquipmentType.BODYWEIGHT,
            "core",
            "corrective",
            "plank",
        ),
        _exercise(
            "Hanging Knee Raise",
            MuscleGroup.CORE,
            EquipmentType.PULL_UP_BAR,
            "core",
            "accessory",
            "leg_raise",
        ),
        _exercise(
            "Cable Wood Chop",
            MuscleGroup.CORE,
            EquipmentType.CABLE_MACHINE,
            "core",
            "accessory",
            "rotation",
        ),
        _exercise(
            "Kettlebell Swing",
            MuscleGroup.LEGS,
            EquipmentType.KETTLEBELL,
            "hinge",
            "secondary_compound",
            "power_hinge",
        ),
        _exercise(
            "Treadmill Zone Two",
            MuscleGroup.CARDIO,
            EquipmentType.TREADMILL,
            "cardio",
            "finisher",
            "treadmill",
        ),
        _exercise(
            "Bike Intervals",
            MuscleGroup.CARDIO,
            EquipmentType.BIKE,
            "cardio",
            "finisher",
            "bike",
        ),
        _exercise(
            "Advanced Barbell Complex",
            MuscleGroup.FULL_BODY,
            EquipmentType.BARBELL,
            "hinge",
            "main_compound",
            "advanced_complex",
            level=TrainingLevel.ADVANCED,
            joint_stress="high",
        ),
    ]


EQUIPMENT = [
    "dumbbell",
    "kettlebell",
    "cable_machine",
    "machine",
    "leg_press",
    "bodyweight",
    "pull_up_bar",
    "treadmill",
    "bike",
]


def _generate(template_id: str, style: str = "balanced"):
    catalog = _catalog()
    plan = RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal="muscle_gain",
        training_level="intermediate",
        readiness_score=75,
        readiness_recommendation="train_normal",
        workout_split="full_body",
        focus_muscle=template_id,
        available_time_minutes=60,
        exercises=catalog,
        avoid_exercises=[],
        available_equipment=EQUIPMENT,
        training_style=style,
    )
    by_id = {item.id: item for item in catalog}
    return plan, [by_id[item.exercise_id] for item in plan.exercises]


def _patterns(exercises: list[Exercise]) -> set[str]:
    return {item.movement_pattern or "" for item in exercises}


def _categories(exercises: list[Exercise]) -> set[str]:
    return {get_equipment_category(item.equipment_type.value) for item in exercises}


def test_equipment_diversity_prevents_single_category_with_gym_equipment() -> None:
    _, exercises = _generate("upper_push_balanced")

    assert len(_categories(exercises)) >= 3
    assert _categories(exercises) != {"bodyweight"}
    assert _categories(exercises) != {"machine"}
    assert "free_weight" in _categories(exercises)


def test_upper_push_balanced_contains_mixed_equipment() -> None:
    _, exercises = _generate("upper_push_balanced")

    assert {"horizontal_push", "vertical_push", "vertical_pull"} <= _patterns(exercises)
    assert {"rear_delt", "elbow_extension"} <= _patterns(exercises)
    assert "cardio" in _patterns(exercises)
    assert {"free_weight", "cable", "cardio"} <= _categories(exercises)


def test_lower_core_contains_squat_hinge_machine_and_core() -> None:
    _, exercises = _generate("lower_core")

    assert {"squat", "hinge", "core"} <= _patterns(exercises)
    assert "machine" in _categories(exercises)
    assert "bodyweight" in _categories(exercises)


def test_upper_pull_posture_contains_balanced_posture_work() -> None:
    _, exercises = _generate("upper_pull_posture")
    patterns = [item.movement_pattern for item in exercises]

    assert patterns.count("horizontal_pull") == 2
    assert {"horizontal_push", "rear_delt", "elbow_flexion"} <= set(patterns)


def test_full_body_conditioning_contains_required_patterns_and_cardio() -> None:
    _, exercises = _generate("full_body_conditioning")

    assert {"lunge", "vertical_pull", "vertical_push", "hinge", "core", "cardio"} <= (
        _patterns(exercises)
    )


def test_conditioning_and_strength_styles_change_cardio_and_prescription() -> None:
    conditioning_plan, conditioning_exercises = _generate(
        "upper_push_balanced", "conditioning"
    )
    strength_plan, strength_exercises = _generate("upper_push_balanced", "strength")

    assert "cardio" in _patterns(conditioning_exercises)
    assert "cardio" not in _patterns(strength_exercises)
    compound_reps = [
        item.target_reps
        for item, exercise in zip(strength_plan.exercises, strength_exercises)
        if exercise.exercise_role in {"main_compound", "secondary_compound"}
    ]
    assert compound_reps
    assert set(compound_reps) == {"5-8"}
    assert all(item.rest_seconds <= 60 for item in conditioning_plan.exercises)


def test_returning_style_caps_rpe_and_avoids_advanced_high_stress() -> None:
    plan, exercises = _generate("full_body_conditioning", "returning")

    assert all(item.target_rpe <= 7 for item in plan.exercises)
    assert all(item.training_level != TrainingLevel.ADVANCED for item in exercises)
    assert all(item.joint_stress != "high" for item in exercises)
