import asyncio
from uuid import uuid4

from sqlmodel import select

from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.session import SessionLocal


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
    ]


async def seed_exercises() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(ExerciseModel.id).limit(1))
        if result.first() is not None:
            return 0

        rows = _seed_rows()
        session.add_all(rows)
        await session.commit()
        return len(rows)


async def main() -> None:
    inserted = await seed_exercises()
    if inserted == 0:
        print("Exercise seed skipped: data already exists")
        return
    print(f"Exercise seed completed: inserted {inserted} records")


if __name__ == "__main__":
    asyncio.run(main())
