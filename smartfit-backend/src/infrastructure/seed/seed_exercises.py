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
            instructions=[
                "Hold one dumbbell close to the chest.",
                "Brace the core and squat until thighs are near parallel.",
                "Drive through mid-foot to stand tall.",
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
            instructions=[
                "Set hands slightly wider than shoulders.",
                "Lower with a rigid torso until the chest nears the floor.",
                "Press back to lockout without losing core tension.",
            ],
            exercise_metadata={"category": "strength", "default_reps": "8-15"},
        ),
        ExerciseModel(
            id=uuid4(),
            slug="treadmill-zone-2-walk",
            name="Treadmill Zone 2 Walk",
            description="Low-intensity aerobic session for recovery and cardiovascular base building.",
            muscle_group=MuscleGroup.CARDIO.value,
            equipment_type=EquipmentType.TREADMILL.value,
            training_level=TrainingLevel.BEGINNER.value,
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
