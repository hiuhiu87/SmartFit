from dataclasses import dataclass, field

from src.domain.common.enums import EquipmentType, Goal, TrainingLevel, WorkoutStyle


@dataclass(slots=True)
class UpdateProfileCommand:
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    training_level: TrainingLevel = TrainingLevel.BEGINNER
    primary_goal: Goal = Goal.GENERAL_HEALTH
    injuries: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class UpdateEquipmentCommand:
    equipment_types: list[EquipmentType]


@dataclass(slots=True)
class UpdatePreferenceCommand:
    workout_style: WorkoutStyle = WorkoutStyle.BALANCED
