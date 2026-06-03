import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.session import SessionLocal

DATASET_URL = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/data/exercises.json"
DATASET_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "exercises-dataset"
    / "exercises.json"
)
SOURCE_NAME = "hasaneyldrm/exercises-dataset"


def load_dataset(source: str | None = None) -> list[dict]:
    source = source or str(DATASET_PATH)
    if source.startswith(("http://", "https://")):
        with urlopen(source, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    with Path(source).expanduser().open("r", encoding="utf-8") as file:
        return json.load(file)


async def import_external_exercises(
    session: AsyncSession,
    records: list[dict],
    *,
    limit: int | None = None,
) -> int:
    statement = select(ExerciseModel.slug)
    result = await session.execute(statement)
    existing_slugs = {slug for (slug,) in result.all()}

    inserted = 0
    for record in records[:limit]:
        model = map_external_exercise(record)
        if model.slug in existing_slugs:
            continue
        session.add(model)
        existing_slugs.add(model.slug)
        inserted += 1

    if inserted:
        await session.commit()
    return inserted


def map_external_exercise(record: dict) -> ExerciseModel:
    name = str(record.get("name") or "").strip()
    external_id = str(record.get("id") or "").strip()
    category = str(record.get("category") or record.get("body_part") or "").strip()
    target = str(record.get("target") or "").strip()
    equipment = str(record.get("equipment") or "").strip()
    instructions = record.get("instructions") or {}
    instruction_steps = record.get("instruction_steps") or {}
    secondary_muscles = record.get("secondary_muscles") or []

    slug = _slugify(f"exdb-{external_id}-{name}" if external_id else f"exdb-{name}")
    primary_muscle = _map_muscle_group(category=category, target=target)
    equipment_type = _map_equipment(equipment)
    movement_type = _infer_movement_type(
        name=name,
        category=category,
        target=target,
        equipment=equipment,
    )
    movement_pattern = _infer_movement_pattern(
        name=name, movement_type=movement_type, target=target
    )

    steps = instruction_steps.get("en") if isinstance(instruction_steps, dict) else None
    if not isinstance(steps, list):
        steps = []

    instruction = None
    if isinstance(instructions, dict):
        instruction = instructions.get("en")

    return ExerciseModel(
        slug=slug,
        name=name.title() if name else f"Exercise {external_id}",
        description=instruction,
        muscle_group=primary_muscle.value,
        equipment_type=equipment_type.value,
        training_level=_infer_training_level(name=name).value,
        secondary_muscles=[
            str(item).strip().lower().replace(" ", "_")
            for item in secondary_muscles
            if str(item).strip()
        ],
        movement_type=movement_type,
        movement_pattern=movement_pattern,
        exercise_role=_infer_exercise_role(
            name=name, movement_pattern=movement_pattern
        ),
        fatigue_level=_infer_fatigue_level(movement_pattern=movement_pattern),
        joint_stress=_infer_joint_stress(name=name, movement_pattern=movement_pattern),
        substitution_group=_infer_substitution_group(
            name=name,
            movement_pattern=movement_pattern,
            equipment_type=equipment_type,
        ),
        instruction=instruction,
        safety_notes=None,
        instructions=[str(item) for item in steps if str(item).strip()],
        exercise_metadata={
            "source": SOURCE_NAME,
            "external_id": external_id,
            "source_category": category,
            "source_body_part": record.get("body_part"),
            "source_equipment": equipment,
            "source_target": target,
            "source_muscle_group": record.get("muscle_group"),
            "image_path": record.get("image"),
            "gif_path": record.get("gif_url"),
            "instructions_tr": (
                instructions.get("tr") if isinstance(instructions, dict) else None
            ),
        },
    )


def _map_muscle_group(category: str, target: str) -> MuscleGroup:
    normalized = f"{category} {target}".lower()
    if any(term in normalized for term in ["chest", "pector"]):
        return MuscleGroup.CHEST
    if any(term in normalized for term in ["back", "lat", "trap", "rhomboid"]):
        return MuscleGroup.BACK
    if any(
        term in normalized
        for term in [
            "upper leg",
            "lower leg",
            "quad",
            "hamstring",
            "glute",
            "calf",
            "adductor",
            "abductor",
        ]
    ):
        return MuscleGroup.LEGS
    if any(term in normalized for term in ["shoulder", "delt"]):
        return MuscleGroup.SHOULDERS
    if any(term in normalized for term in ["arm", "bicep", "tricep", "forearm"]):
        return MuscleGroup.ARMS
    if any(term in normalized for term in ["waist", "abs", "oblique", "core"]):
        return MuscleGroup.CORE
    if "cardio" in normalized:
        return MuscleGroup.CARDIO
    if any(term in normalized for term in ["neck", "stretch", "mobility"]):
        return MuscleGroup.MOBILITY
    return MuscleGroup.FULL_BODY


def _map_equipment(equipment: str) -> EquipmentType:
    normalized = equipment.lower()
    if "dumbbell" in normalized:
        return EquipmentType.DUMBBELL
    if "barbell" in normalized or "ez barbell" in normalized:
        return EquipmentType.BARBELL
    if "cable" in normalized:
        return EquipmentType.CABLE_MACHINE
    if "smith" in normalized:
        return EquipmentType.SMITH_MACHINE
    if "band" in normalized:
        return EquipmentType.RESISTANCE_BAND
    if (
        "stationary bike" in normalized
        or "bike" in normalized
        or "bicycle" in normalized
    ):
        return EquipmentType.BIKE
    if "treadmill" in normalized or "elliptical" in normalized:
        return EquipmentType.TREADMILL
    if "body weight" in normalized or "bodyweight" in normalized:
        return EquipmentType.BODYWEIGHT
    if any(term in normalized for term in ["machine", "leverage", "sled"]):
        return EquipmentType.MACHINE
    if "bench" in normalized:
        return EquipmentType.BENCH
    return EquipmentType.BODYWEIGHT


def _infer_movement_type(name: str, category: str, target: str, equipment: str) -> str:
    normalized = f"{name} {category} {target} {equipment}".lower()
    if any(
        term in normalized for term in ["run", "walk", "bike", "cardio", "elliptical"]
    ):
        return "cardio"
    if any(term in normalized for term in ["stretch", "mobility", "circle"]):
        return "mobility"
    if any(term in normalized for term in ["squat", "lunge", "leg press", "step-up"]):
        return "squat"
    if any(
        term in normalized
        for term in ["deadlift", "hinge", "hip thrust", "good morning", "glute bridge"]
    ):
        return "hinge"
    if any(
        term in normalized
        for term in ["row", "pull", "pulldown", "chin-up", "chin up", "curl"]
    ):
        return "pull"
    if any(term in normalized for term in ["press", "push", "dip", "extension", "fly"]):
        return "push"
    if any(
        term in normalized
        for term in ["sit-up", "crunch", "plank", "abs", "oblique", "waist"]
    ):
        return "core"
    return "general"


def _infer_training_level(name: str) -> TrainingLevel:
    normalized = name.lower()
    if any(
        term in normalized
        for term in ["one arm", "single arm", "weighted", "archer", "handstand"]
    ):
        return TrainingLevel.ADVANCED
    if any(term in normalized for term in ["barbell", "smith", "cable", "machine"]):
        return TrainingLevel.INTERMEDIATE
    return TrainingLevel.BEGINNER


def _infer_movement_pattern(name: str, movement_type: str, target: str) -> str:
    normalized = f"{name} {target}".lower()
    if any(term in normalized for term in ["pulldown", "pull up", "pull-up", "chin"]):
        return "vertical_pull"
    if "row" in normalized:
        return "horizontal_pull"
    if any(
        term in normalized
        for term in ["shoulder press", "overhead press", "military press"]
    ):
        return "vertical_push"
    if any(
        term in normalized
        for term in ["bench press", "chest press", "push up", "push-up"]
    ):
        return "horizontal_push"
    if "lunge" in normalized:
        return "lunge"
    if "curl" in normalized:
        return "elbow_flexion"
    if any(term in normalized for term in ["triceps", "extension", "pushdown"]):
        return "elbow_extension"
    if any(term in normalized for term in ["rear delt", "face pull"]):
        return "rear_delt"
    if movement_type in {"squat", "hinge", "core", "cardio", "mobility"}:
        return movement_type
    if movement_type == "pull":
        return "horizontal_pull"
    if movement_type == "push":
        return "horizontal_push"
    return "mobility"


def _infer_exercise_role(name: str, movement_pattern: str) -> str:
    normalized = name.lower()
    if movement_pattern == "cardio":
        return "finisher"
    if movement_pattern in {"mobility", "core", "rear_delt"}:
        return "corrective"
    if movement_pattern in {"elbow_flexion", "elbow_extension"}:
        return "isolation"
    if any(
        term in normalized for term in ["barbell", "deadlift", "squat", "bench press"]
    ):
        return "main_compound"
    return "secondary_compound"


def _infer_fatigue_level(movement_pattern: str) -> str:
    if movement_pattern in {"squat", "hinge"}:
        return "high"
    if movement_pattern in {
        "cardio",
        "horizontal_pull",
        "horizontal_push",
        "vertical_pull",
        "vertical_push",
    }:
        return "medium"
    return "low"


def _infer_joint_stress(name: str, movement_pattern: str) -> str:
    normalized = name.lower()
    if any(term in normalized for term in ["machine", "supported", "walk", "mobility"]):
        return "low"
    if movement_pattern in {"squat", "hinge", "vertical_push"}:
        return "medium"
    return "low"


def _infer_substitution_group(
    name: str, movement_pattern: str, equipment_type: EquipmentType
) -> str:
    normalized = name.lower()
    if movement_pattern == "horizontal_pull":
        return "row"
    if movement_pattern == "horizontal_push":
        return "chest_press"
    if movement_pattern == "vertical_pull":
        return "vertical_pull"
    if movement_pattern == "vertical_push":
        return "overhead_press"
    if movement_pattern == "elbow_flexion":
        return "biceps_curl"
    if movement_pattern == "elbow_extension":
        return "triceps_extension"
    if movement_pattern == "cardio":
        if equipment_type == EquipmentType.BIKE:
            return "bike_cardio"
        if equipment_type == EquipmentType.TREADMILL:
            return "treadmill_cardio"
    if "lunge" in normalized:
        return "lunge"
    return movement_pattern


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import exercises from hasaneyldrm/exercises-dataset."
    )
    parser.add_argument(
        "--source", default=str(DATASET_PATH), help="JSON file path or URL."
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Optional max records to import."
    )
    args = parser.parse_args()

    records = load_dataset(args.source)
    async with SessionLocal() as session:
        inserted = await import_external_exercises(session, records, limit=args.limit)
    print(f"Imported {inserted} external exercises.")


if __name__ == "__main__":
    asyncio.run(main())
