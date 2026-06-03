from uuid import NAMESPACE_DNS, uuid4, uuid5

from src.domain.common.enums import EquipmentType, Goal, MuscleGroup, TrainingLevel
from src.domain.exercise.entities import Exercise
from src.domain.workout.exercise_selection_policy import ExerciseSelectionPolicy
from src.domain.workout.services import RuleBasedWorkoutGenerator
from src.domain.workout.template_resolver import WorkoutTemplateResolver
from src.domain.workout.templates import BUILT_IN_TEMPLATES


def exercise(
    name: str,
    muscle_group: MuscleGroup,
    equipment: EquipmentType,
    level: TrainingLevel,
    movement_pattern: str,
    role: str,
    substitution_group: str,
) -> Exercise:
    return Exercise(
        id=uuid5(NAMESPACE_DNS, name),
        slug=name.lower().replace(" ", "-"),
        name=name,
        muscle_group=muscle_group,
        equipment_type=equipment,
        training_level=level,
        movement_type=movement_pattern,
        movement_pattern=movement_pattern,
        exercise_role=role,
        fatigue_level="medium",
        joint_stress="low",
        substitution_group=substitution_group,
        is_active=True,
    )


def candidate_exercises() -> list[Exercise]:
    return [
        exercise(
            "Barbell Back Squat",
            MuscleGroup.LEGS,
            EquipmentType.BARBELL,
            TrainingLevel.BEGINNER,
            "squat",
            "main_compound",
            "squat",
        ),
        exercise(
            "Conventional Deadlift",
            MuscleGroup.LEGS,
            EquipmentType.BARBELL,
            TrainingLevel.BEGINNER,
            "hinge",
            "main_compound",
            "hinge",
        ),
        exercise(
            "Bent Over Row",
            MuscleGroup.BACK,
            EquipmentType.BARBELL,
            TrainingLevel.INTERMEDIATE,
            "horizontal_pull",
            "main_compound",
            "row",
        ),
        exercise(
            "Chest Supported Dumbbell Row",
            MuscleGroup.BACK,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "horizontal_pull",
            "secondary_compound",
            "row",
        ),
        exercise(
            "Lat Pulldown",
            MuscleGroup.BACK,
            EquipmentType.CABLE_MACHINE,
            TrainingLevel.BEGINNER,
            "vertical_pull",
            "secondary_compound",
            "vertical_pull",
        ),
        exercise(
            "Push-Up",
            MuscleGroup.CHEST,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "horizontal_push",
            "secondary_compound",
            "chest_press",
        ),
        exercise(
            "Dumbbell Rear Delt Fly",
            MuscleGroup.SHOULDERS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "rear_delt",
            "corrective",
            "rear_delt",
        ),
        exercise(
            "Dumbbell Biceps Curl",
            MuscleGroup.ARMS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "elbow_flexion",
            "isolation",
            "biceps_curl",
        ),
        exercise(
            "Bike HIIT Intervals",
            MuscleGroup.CARDIO,
            EquipmentType.BIKE,
            TrainingLevel.INTERMEDIATE,
            "cardio",
            "finisher",
            "bike_cardio",
        ),
        exercise(
            "Handstand Push-Up",
            MuscleGroup.SHOULDERS,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.ADVANCED,
            "vertical_push",
            "main_compound",
            "overhead_press",
        ),
        exercise(
            "Goblet Squat",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "squat",
            "main_compound",
            "squat",
        ),
        exercise(
            "Romanian Deadlift",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "hinge",
            "secondary_compound",
            "hinge",
        ),
        exercise(
            "Dumbbell Lunge",
            MuscleGroup.LEGS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "lunge",
            "secondary_compound",
            "lunge",
        ),
        exercise(
            "Plank",
            MuscleGroup.CORE,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "core",
            "corrective",
            "core",
        ),
        exercise(
            "Easy Walk",
            MuscleGroup.CARDIO,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "cardio",
            "corrective",
            "walking_cardio",
        ),
        exercise(
            "Standing Mobility Flow",
            MuscleGroup.MOBILITY,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "mobility",
            "corrective",
            "mobility",
        ),
    ]


def legacy_exercise(
    name: str,
    muscle_group: MuscleGroup,
    equipment: EquipmentType,
    movement_type: str,
) -> Exercise:
    return Exercise(
        id=uuid5(NAMESPACE_DNS, f"legacy-{name}"),
        slug=name.lower().replace(" ", "-"),
        name=name,
        muscle_group=muscle_group,
        equipment_type=equipment,
        training_level=TrainingLevel.BEGINNER,
        movement_type=movement_type,
        is_active=True,
    )


def legacy_candidate_exercises() -> list[Exercise]:
    return [
        legacy_exercise("Dumbbell Bench Press", MuscleGroup.CHEST, EquipmentType.DUMBBELL, "push"),
        legacy_exercise("Push-Up", MuscleGroup.CHEST, EquipmentType.BODYWEIGHT, "push"),
        legacy_exercise("Dumbbell Shoulder Press", MuscleGroup.SHOULDERS, EquipmentType.DUMBBELL, "push"),
        legacy_exercise("Dumbbell Lateral Raise", MuscleGroup.SHOULDERS, EquipmentType.DUMBBELL, "push"),
        legacy_exercise("Dumbbell Triceps Extension", MuscleGroup.ARMS, EquipmentType.DUMBBELL, "push"),
        legacy_exercise("Dumbbell One-Arm Row", MuscleGroup.BACK, EquipmentType.DUMBBELL, "pull"),
        legacy_exercise("Chest Supported Dumbbell Row", MuscleGroup.BACK, EquipmentType.DUMBBELL, "pull"),
        legacy_exercise("Dumbbell Biceps Curl", MuscleGroup.ARMS, EquipmentType.DUMBBELL, "pull"),
        legacy_exercise("Plank", MuscleGroup.CORE, EquipmentType.BODYWEIGHT, "core"),
    ]


def generate(
    readiness: int,
    focus: str | None = "upper_body_pull",
    equipment: list[str] | None = None,
    avoid: list[str] | None = None,
    level: str = TrainingLevel.INTERMEDIATE.value,
    time: int = 60,
    goal: str = Goal.MUSCLE_GAIN.value,
):
    return RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=goal,
        training_level=level,
        readiness_score=readiness,
        readiness_recommendation="train_normal",
        workout_split="upper_body",
        focus_muscle=focus,
        available_time_minutes=time,
        exercises=candidate_exercises(),
        avoid_exercises=avoid or [],
        available_equipment=equipment
        or ["barbell", "dumbbell", "bench", "bodyweight", "bike"],
    )


def generate_with_exercises(
    exercises: list[Exercise],
    readiness: int = 70,
    focus: str | None = "upper_body_push",
    equipment: list[str] | None = None,
    level: str = TrainingLevel.BEGINNER.value,
    time: int = 60,
):
    return RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=Goal.MUSCLE_GAIN.value,
        training_level=level,
        readiness_score=readiness,
        readiness_recommendation="train_normal",
        workout_split="upper_body",
        focus_muscle=focus,
        available_time_minutes=time,
        exercises=exercises,
        avoid_exercises=[],
        available_equipment=equipment or ["dumbbell", "bench", "bodyweight"],
    )


def test_template_resolver_maps_upper_pull_and_low_readiness() -> None:
    resolver = WorkoutTemplateResolver()
    assert (
        resolver.resolve("upper_body_pull", "muscle_gain", "intermediate", 72).id
        == "upper_pull_emphasis"
    )
    assert (
        resolver.resolve("back", "muscle_gain", "intermediate", 72).id
        == "upper_pull_emphasis"
    )
    assert (
        resolver.resolve("chest", "muscle_gain", "intermediate", 72).id
        == "upper_push_emphasis"
    )
    assert (
        resolver.resolve(None, "general_health", "beginner", 72).id
        == "full_body_beginner"
    )
    assert (
        resolver.resolve("upper_body_pull", "muscle_gain", "intermediate", 35).id
        == "recovery_session"
    )


def test_policy_respects_equipment_avoid_and_beginner_advanced_block() -> None:
    policy = ExerciseSelectionPolicy()
    slot = BUILT_IN_TEMPLATES["upper_pull_emphasis"].slots[0]
    selected = policy.select_exercise_for_slot(
        slot=slot,
        candidates=candidate_exercises(),
        available_equipment=["barbell", "dumbbell", "bodyweight"],
        training_level=TrainingLevel.BEGINNER.value,
        avoid_exercises=["Bent Over Row"],
        already_selected=[],
        template_id="upper_pull_emphasis",
    )
    assert selected is not None
    assert selected.name != "Bent Over Row"
    assert selected.name == "Chest Supported Dumbbell Row"
    assert selected.training_level != TrainingLevel.ADVANCED


def test_upper_pull_emphasis_generates_realistic_structure() -> None:
    plan = generate(72)
    names = [item.exercise_id for item in plan.exercises]
    assert len(plan.exercises) == 6
    assert len(names) == len(set(names))
    assert plan.focus.value == "upper_body_pull"
    assert plan.estimated_duration_minutes == 60
    assert any(item.target_reps == "30s fast / 60s easy" for item in plan.exercises)


def test_low_readiness_removes_hiit() -> None:
    plan = generate(35)
    assert plan.decision == "recovery"
    assert all(item.target_rpe <= 7 for item in plan.exercises)
    assert all(item.target_reps != "30s fast / 60s easy" for item in plan.exercises)


def test_very_low_readiness_recovery_session() -> None:
    plan = generate(15)
    assert plan.decision == "recovery"
    assert all(item.target_rpe <= 3 for item in plan.exercises)
    assert len(plan.exercises) <= 3


def test_beginner_avoids_advanced_exercises() -> None:
    plan = generate(72, focus="upper_body", level=TrainingLevel.BEGINNER.value)
    selected_ids = {item.exercise_id for item in plan.exercises}
    advanced_ids = {
        item.id
        for item in candidate_exercises()
        if item.training_level == TrainingLevel.ADVANCED
    }
    assert selected_ids.isdisjoint(advanced_ids)


def test_equipment_filter_respected() -> None:
    plan = generate(72, equipment=["dumbbell", "bodyweight"])
    allowed_ids = {
        item.id
        for item in candidate_exercises()
        if item.equipment_type in {EquipmentType.DUMBBELL, EquipmentType.BODYWEIGHT}
    }
    assert {item.exercise_id for item in plan.exercises}.issubset(allowed_ids)


def test_avoid_exercises_respected() -> None:
    plan = generate(72, avoid=["Bent Over Row"])
    avoided = next(
        item.id for item in candidate_exercises() if item.name == "Bent Over Row"
    )
    assert avoided not in {item.exercise_id for item in plan.exercises}


def test_normal_upper_body_not_only_three_exercises() -> None:
    plan = generate(70, focus="upper_body", time=60)
    assert len(plan.exercises) >= 5
    assert plan.estimated_duration_minutes == 60


def test_requested_duration_is_preserved_for_normal_rule_based_plan() -> None:
    plan = generate(70, focus="upper_body_pull", time=45)
    assert plan.estimated_duration_minutes == 45


def test_sixty_minute_push_plan_fills_with_legacy_metadata() -> None:
    plan = generate_with_exercises(legacy_candidate_exercises(), focus="chest", time=60)
    names = [item.exercise_id for item in plan.exercises]
    assert plan.estimated_duration_minutes == 60
    assert len(plan.exercises) >= 6
    assert len(names) == len(set(names))


def test_lean_goal_uses_higher_reps_short_rest_and_cardio_last() -> None:
    plan = generate(
        72,
        focus="upper_body_pull",
        goal=Goal.FAT_LOSS.value,
        equipment=["barbell", "dumbbell", "bench", "bodyweight", "bike"],
        time=60,
    )
    assert plan.exercises[-1].target_reps == "10-15 minutes"
    for item in plan.exercises[:-1]:
        if item.target_reps != "30-45 seconds":
            assert item.target_reps == "12-15"
        assert (item.rest_seconds or 0) <= 60


def test_workout_split_drives_template_when_focus_missing() -> None:
    plan = RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=Goal.MUSCLE_GAIN.value,
        training_level=TrainingLevel.INTERMEDIATE.value,
        readiness_score=72,
        readiness_recommendation="train_normal",
        workout_split="pull",
        focus_muscle=None,
        available_time_minutes=60,
        exercises=candidate_exercises(),
        avoid_exercises=[],
        available_equipment=["barbell", "dumbbell", "bench", "bodyweight", "bike"],
    )
    assert plan.focus.value == "upper_body_pull"
    assert len(plan.exercises) >= 6


def test_beginner_lean_excludes_heavy_barbell_squat_and_deadlift() -> None:
    plan = generate(
        72,
        focus="lower_body",
        goal=Goal.FAT_LOSS.value,
        level=TrainingLevel.BEGINNER.value,
        equipment=["barbell", "dumbbell", "bodyweight"],
        time=60,
    )
    selected_ids = {item.exercise_id for item in plan.exercises}
    heavy_ids = {
        item.id
        for item in candidate_exercises()
        if item.name in {"Barbell Back Squat", "Conventional Deadlift"}
    }
    assert selected_ids.isdisjoint(heavy_ids)


def test_sixty_minute_pull_plan_fills_without_cardio_equipment() -> None:
    plan = generate_with_exercises(
        legacy_candidate_exercises(),
        focus="upper_body_pull",
        equipment=["dumbbell", "bodyweight"],
        level=TrainingLevel.BEGINNER.value,
        time=60,
    )
    names = [item.exercise_id for item in plan.exercises]
    assert plan.estimated_duration_minutes == 60
    assert len(plan.exercises) >= 6
    assert len(names) == len(set(names))
