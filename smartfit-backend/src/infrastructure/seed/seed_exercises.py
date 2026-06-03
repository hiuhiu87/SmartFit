import asyncio
from uuid import uuid4

from sqlmodel import select

from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.seed.external_exercise_dataset import (
    load_dataset,
    import_external_exercises,
)


def _exercise(
    slug: str,
    name: str,
    muscle_group: MuscleGroup,
    equipment_type: EquipmentType,
    training_level: TrainingLevel,
    movement_type: str,
    movement_pattern: str,
    exercise_role: str,
    fatigue_level: str,
    joint_stress: str,
    substitution_group: str,
    default_reps: str,
    secondary_muscles: list[str] | None = None,
    description: str | None = None,
) -> ExerciseModel:
    return ExerciseModel(
        id=uuid4(),
        slug=slug,
        name=name,
        description=description
        or f"{name} programmed for structured SmartFit workouts.",
        muscle_group=muscle_group.value,
        equipment_type=equipment_type.value,
        training_level=training_level.value,
        secondary_muscles=secondary_muscles or [],
        movement_type=movement_type,
        movement_pattern=movement_pattern,
        exercise_role=exercise_role,
        fatigue_level=fatigue_level,
        joint_stress=joint_stress,
        substitution_group=substitution_group,
        instruction=f"Perform {name} with controlled tempo and pain-free range of motion.",
        safety_notes="Stop or reduce load if form breaks down or pain appears.",
        instructions=[
            "Set up with stable posture and brace before starting.",
            "Move through a controlled range of motion.",
            "Return to the start position without rushing.",
        ],
        exercise_metadata={"category": "strength", "default_reps": default_reps},
    )


def _seed_rows() -> list[ExerciseModel]:
    return [
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-goblet-squat",
            name="Dumbbell Goblet Squat",
            description="A squat variation that is accessible for most users training at home or in a gym.",
            muscle_group=MuscleGroup.LEGS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["glutes", "core"],
            movement_type="squat",
            instruction="Hold one dumbbell at chest level and squat with a braced torso.",
            safety_notes="Keep the chest lifted and avoid collapsing the knees inward.",
            instructions=[
                "Hold one dumbbell close to the chest.",
                "Brace the core and squat until thighs are near parallel.",
                "Drive through mid-foot to stand tall.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-bench-press",
            name="Dumbbell Bench Press",
            description="A beginner-friendly pressing pattern for chest and triceps development.",
            muscle_group=MuscleGroup.CHEST.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["triceps", "shoulders"],
            movement_type="push",
            instruction="Lie on a bench and press dumbbells upward with control.",
            safety_notes="Keep shoulder blades stable and avoid flaring elbows too wide.",
            instructions=[
                "Set shoulder blades and feet before unracking.",
                "Lower dumbbells to a comfortable chest-level position.",
                "Press back up while keeping wrists stacked over elbows.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="push-up",
            name="Push-Up",
            description="Classic bodyweight push exercise for chest, shoulders, and triceps.",
            muscle_group=MuscleGroup.CHEST.value,
            equipment_type=EquipmentType.BODYWEIGHT.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["triceps", "shoulders", "core"],
            movement_type="push",
            instruction="Lower your chest under control and press back up in one line.",
            safety_notes="Do not let the hips sag or the head jut forward.",
            instructions=[
                "Set hands slightly wider than shoulders.",
                "Lower with a rigid torso until the chest nears the floor.",
                "Press back to lockout without losing core tension.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="seated-cable-row",
            name="Seated Cable Row",
            description="Horizontal pull pattern for upper back and lat development.",
            muscle_group=MuscleGroup.BACK.value,
            equipment_type=EquipmentType.CABLE_MACHINE.value,
            training_level=TrainingLevel.INTERMEDIATE.value,
            secondary_muscles=["biceps", "rear_delts"],
            movement_type="pull",
            instruction="Pull the handle toward your torso while keeping the spine tall.",
            safety_notes="Do not jerk the torso backward to finish the rep.",
            instructions=[
                "Sit tall with feet braced against the platform.",
                "Initiate by pulling elbows back and squeezing the shoulder blades.",
                "Return the handle with control without rounding the back.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-incline-press",
            name="Dumbbell Incline Press",
            description="Incline dumbbell press for upper chest and shoulders.",
            muscle_group=MuscleGroup.CHEST.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["shoulders", "triceps"],
            movement_type="push",
            instruction="Press dumbbells from an incline bench with controlled shoulder position.",
            safety_notes="Keep elbows slightly tucked and avoid bouncing at the bottom.",
            instructions=[
                "Set the bench to a moderate incline.",
                "Lower dumbbells until elbows are just below shoulder height.",
                "Press up smoothly without shrugging.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-shoulder-press",
            name="Dumbbell Shoulder Press",
            description="Vertical pressing pattern for shoulders and triceps.",
            muscle_group=MuscleGroup.SHOULDERS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["triceps", "core"],
            movement_type="push",
            instruction="Press dumbbells overhead while keeping ribs down.",
            safety_notes="Do not arch the lower back to finish the rep.",
            instructions=[
                "Start with dumbbells at shoulder height.",
                "Brace the core and press overhead.",
                "Lower under control back to shoulders.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-lateral-raise",
            name="Dumbbell Lateral Raise",
            description="Shoulder accessory exercise for side delts.",
            muscle_group=MuscleGroup.SHOULDERS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=[],
            movement_type="push",
            instruction="Raise dumbbells to shoulder height with soft elbows.",
            safety_notes="Use a light load and avoid swinging.",
            instructions=[
                "Stand tall with dumbbells at your sides.",
                "Raise arms out to shoulder height.",
                "Lower slowly without losing posture.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "12-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-one-arm-row",
            name="Dumbbell One-Arm Row",
            description="Single-arm row for lats and upper back.",
            muscle_group=MuscleGroup.BACK.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["biceps", "rear_delts"],
            movement_type="pull",
            instruction="Row one dumbbell toward the hip while bracing on a bench.",
            safety_notes="Keep the spine neutral and avoid twisting.",
            instructions=[
                "Brace one hand and knee on a bench.",
                "Pull the dumbbell toward your hip.",
                "Lower until the arm is long without rounding.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-romanian-deadlift",
            name="Dumbbell Romanian Deadlift",
            description="Hip hinge pattern for hamstrings and glutes.",
            muscle_group=MuscleGroup.LEGS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["glutes", "back"],
            movement_type="hinge",
            instruction="Hinge at the hips while keeping dumbbells close to the legs.",
            safety_notes="Stop the descent before the lower back rounds.",
            instructions=[
                "Stand with dumbbells in front of thighs.",
                "Push hips back with a soft knee bend.",
                "Drive hips forward to stand tall.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-12"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-reverse-lunge",
            name="Dumbbell Reverse Lunge",
            description="Unilateral lower-body exercise for quads and glutes.",
            muscle_group=MuscleGroup.LEGS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["glutes", "core"],
            movement_type="squat",
            instruction="Step backward into a lunge and return with control.",
            safety_notes="Keep the front knee tracking over the mid-foot.",
            instructions=[
                "Hold dumbbells at your sides.",
                "Step one foot backward and lower under control.",
                "Drive through the front foot to return.",
            ],
            exercise_metadata={
                "category": "strength",
                "default_reps": "8-10 each side",
            },
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-biceps-curl",
            name="Dumbbell Biceps Curl",
            description="Arm accessory exercise for biceps.",
            muscle_group=MuscleGroup.ARMS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=[],
            movement_type="pull",
            instruction="Curl dumbbells without swinging the torso.",
            safety_notes="Keep wrists neutral and use a controlled tempo.",
            instructions=[
                "Start with arms long at your sides.",
                "Curl dumbbells toward shoulders.",
                "Lower slowly to full arm length.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "10-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dumbbell-triceps-extension",
            name="Dumbbell Triceps Extension",
            description="Arm accessory exercise for triceps.",
            muscle_group=MuscleGroup.ARMS.value,
            equipment_type=EquipmentType.DUMBBELL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["shoulders"],
            movement_type="push",
            instruction="Extend a dumbbell overhead while keeping elbows stable.",
            safety_notes="Use a pain-free range and avoid flaring elbows wide.",
            instructions=[
                "Hold one dumbbell overhead.",
                "Bend elbows to lower behind the head.",
                "Extend elbows to return overhead.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "10-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="bodyweight-squat",
            name="Bodyweight Squat",
            description="No-equipment squat pattern for lower-body training.",
            muscle_group=MuscleGroup.LEGS.value,
            equipment_type=EquipmentType.BODYWEIGHT.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["glutes", "core"],
            movement_type="squat",
            instruction="Squat with control while keeping the chest tall.",
            safety_notes="Avoid knees collapsing inward.",
            instructions=[
                "Stand with feet around shoulder width.",
                "Sit hips down and back.",
                "Stand tall through the mid-foot.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "10-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="glute-bridge",
            name="Glute Bridge",
            description="Bodyweight posterior-chain exercise for glutes.",
            muscle_group=MuscleGroup.LEGS.value,
            equipment_type=EquipmentType.BODYWEIGHT.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["hamstrings", "core"],
            movement_type="hinge",
            instruction="Bridge hips up while keeping ribs down.",
            safety_notes="Do not overextend the lower back at the top.",
            instructions=[
                "Lie on your back with knees bent.",
                "Drive through heels and lift hips.",
                "Lower with control.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "12-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="plank",
            name="Plank",
            description="Core stability exercise.",
            muscle_group=MuscleGroup.CORE.value,
            equipment_type=EquipmentType.BODYWEIGHT.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=["shoulders", "glutes"],
            movement_type="core",
            instruction="Hold a straight line from shoulders to ankles.",
            safety_notes="Stop if the lower back sags or hurts.",
            instructions=[
                "Set elbows under shoulders.",
                "Brace abs and glutes.",
                "Hold steady without dropping hips.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "30-45 seconds"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="dead-bug",
            name="Dead Bug",
            description="Core control exercise for trunk stability.",
            muscle_group=MuscleGroup.CORE.value,
            equipment_type=EquipmentType.BODYWEIGHT.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=[],
            movement_type="core",
            instruction="Move opposite arm and leg while keeping the lower back stable.",
            safety_notes="Keep the movement slow and pain-free.",
            instructions=[
                "Lie on your back with arms and legs raised.",
                "Lower opposite arm and leg slowly.",
                "Return and alternate sides.",
            ],
            exercise_metadata={
                "category": "strength",
                "default_reps": "8-10 each side",
            },
        ),
        ExerciseModel(
            id=uuid4(),
            slug="treadmill-zone-2-walk",
            name="Treadmill Zone 2 Walk",
            description="Low-intensity aerobic session for recovery and cardiovascular base building.",
            muscle_group=MuscleGroup.CARDIO.value,
            equipment_type=EquipmentType.TREADMILL.value,
            training_level=TrainingLevel.BEGINNER.value,
            secondary_muscles=[],
            movement_type="cardio",
            instruction="Walk at a sustainable conversational pace for the target duration.",
            safety_notes="Use the rails only for balance, not to unload the movement.",
            instructions=[
                "Choose a pace that keeps effort conversational.",
                "Maintain steady breathing for the target duration.",
                "Reduce speed gradually in the final minutes.",
            ],
            exercise_metadata={"category": "cardio", "default_duration_minutes": "20"},
        ),
        _exercise(
            "barbell-bent-over-row",
            "Bent Over Row",
            MuscleGroup.BACK,
            EquipmentType.BARBELL,
            TrainingLevel.INTERMEDIATE,
            "pull",
            "horizontal_pull",
            "main_compound",
            "high",
            "medium",
            "row",
            "8-12",
            ["biceps", "rear_delts"],
        ),
        _exercise(
            "chest-supported-dumbbell-row",
            "Chest Supported Dumbbell Row",
            MuscleGroup.BACK,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "pull",
            "horizontal_pull",
            "secondary_compound",
            "medium",
            "low",
            "row",
            "10-12",
            ["biceps", "rear_delts"],
        ),
        _exercise(
            "lat-pulldown",
            "Lat Pulldown",
            MuscleGroup.BACK,
            EquipmentType.CABLE_MACHINE,
            TrainingLevel.BEGINNER,
            "pull",
            "vertical_pull",
            "secondary_compound",
            "medium",
            "low",
            "vertical_pull",
            "10-12",
            ["biceps"],
        ),
        _exercise(
            "machine-chest-press",
            "Machine Chest Press",
            MuscleGroup.CHEST,
            EquipmentType.MACHINE,
            TrainingLevel.BEGINNER,
            "push",
            "horizontal_push",
            "secondary_compound",
            "medium",
            "low",
            "chest_press",
            "8-12",
            ["triceps", "shoulders"],
        ),
        _exercise(
            "dumbbell-rear-delt-fly",
            "Dumbbell Rear Delt Fly",
            MuscleGroup.SHOULDERS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "pull",
            "rear_delt",
            "corrective",
            "low",
            "low",
            "rear_delt",
            "12-15",
            ["rear_delts", "upper_back"],
        ),
        _exercise(
            "face-pull",
            "Face Pull",
            MuscleGroup.SHOULDERS,
            EquipmentType.CABLE_MACHINE,
            TrainingLevel.BEGINNER,
            "pull",
            "rear_delt",
            "corrective",
            "low",
            "low",
            "rear_delt",
            "12-15",
            ["rear_delts", "upper_back"],
        ),
        _exercise(
            "hammer-curl",
            "Hammer Curl",
            MuscleGroup.ARMS,
            EquipmentType.DUMBBELL,
            TrainingLevel.BEGINNER,
            "pull",
            "elbow_flexion",
            "isolation",
            "low",
            "low",
            "biceps_curl",
            "10-12",
            ["forearms"],
        ),
        _exercise(
            "triceps-rope-pushdown",
            "Triceps Rope Pushdown",
            MuscleGroup.ARMS,
            EquipmentType.CABLE_MACHINE,
            TrainingLevel.BEGINNER,
            "push",
            "elbow_extension",
            "isolation",
            "low",
            "low",
            "triceps_extension",
            "10-12",
        ),
        _exercise(
            "leg-press",
            "Leg Press",
            MuscleGroup.LEGS,
            EquipmentType.MACHINE,
            TrainingLevel.BEGINNER,
            "squat",
            "squat",
            "main_compound",
            "high",
            "medium",
            "squat",
            "8-12",
            ["glutes"],
        ),
        _exercise(
            "hip-thrust",
            "Hip Thrust",
            MuscleGroup.LEGS,
            EquipmentType.BARBELL,
            TrainingLevel.INTERMEDIATE,
            "hinge",
            "hinge",
            "accessory",
            "medium",
            "low",
            "hinge",
            "10-12",
            ["glutes", "hamstrings"],
        ),
        _exercise(
            "pallof-press",
            "Pallof Press",
            MuscleGroup.CORE,
            EquipmentType.RESISTANCE_BAND,
            TrainingLevel.BEGINNER,
            "core",
            "core",
            "corrective",
            "low",
            "low",
            "core",
            "8-12 each side",
            ["obliques"],
        ),
        _exercise(
            "bike-hiit-intervals",
            "Bike HIIT Intervals",
            MuscleGroup.CARDIO,
            EquipmentType.BIKE,
            TrainingLevel.INTERMEDIATE,
            "cardio",
            "cardio",
            "finisher",
            "medium",
            "low",
            "bike_cardio",
            "30s fast / 60s easy",
        ),
        _exercise(
            "incline-treadmill-walk",
            "Incline Treadmill Walk",
            MuscleGroup.CARDIO,
            EquipmentType.TREADMILL,
            TrainingLevel.BEGINNER,
            "cardio",
            "cardio",
            "finisher",
            "low",
            "low",
            "treadmill_cardio",
            "10-20 minutes easy",
        ),
        _exercise(
            "easy-walk",
            "Easy Walk",
            MuscleGroup.CARDIO,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "cardio",
            "cardio",
            "corrective",
            "low",
            "low",
            "walking_cardio",
            "10-20 minutes easy",
        ),
        _exercise(
            "standing-mobility-flow",
            "Standing Mobility Flow",
            MuscleGroup.MOBILITY,
            EquipmentType.BODYWEIGHT,
            TrainingLevel.BEGINNER,
            "mobility",
            "mobility",
            "corrective",
            "low",
            "low",
            "mobility",
            "5-8 minutes",
        ),
    ]


async def seed_exercises() -> int:
    async with SessionLocal() as session:
        rows = _seed_rows()
        result = await session.execute(select(ExerciseModel))
        existing_by_slug = {row.slug: row for row in result.scalars().all()}
        new_rows = [row for row in rows if row.slug not in existing_by_slug]
        updated = 0
        for row in rows:
            existing = existing_by_slug.get(row.slug)
            if existing is None:
                continue
            updated += _backfill_programming_metadata(existing, row)

        inserted = 0
        if not new_rows:
            inserted = 0
        else:
            session.add_all(new_rows)
            inserted = len(new_rows)
        if inserted or updated:
            await session.commit()

        try:
            external_records = load_dataset()
            inserted += await import_external_exercises(session, external_records)
        except Exception as exc:
            print(f"External exercise dataset import skipped: {exc}")
        return inserted


def _backfill_programming_metadata(
    existing: ExerciseModel, seeded: ExerciseModel
) -> int:
    updated = 0
    for field_name in (
        "movement_pattern",
        "exercise_role",
        "fatigue_level",
        "joint_stress",
        "substitution_group",
    ):
        if (
            getattr(existing, field_name) is None
            and getattr(seeded, field_name) is not None
        ):
            setattr(existing, field_name, getattr(seeded, field_name))
            updated += 1
    if existing.exercise_metadata and seeded.exercise_metadata:
        metadata = dict(existing.exercise_metadata)
        for key, value in seeded.exercise_metadata.items():
            if key not in metadata and value is not None:
                metadata[key] = value
                updated += 1
        existing.exercise_metadata = metadata
    return updated


async def main() -> None:
    inserted = await seed_exercises()
    if inserted == 0:
        print("Exercise seed skipped: data already exists")
        return
    print(f"Exercise seed completed: inserted {inserted} records")


if __name__ == "__main__":
    asyncio.run(main())
