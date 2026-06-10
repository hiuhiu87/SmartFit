from dataclasses import dataclass, field

from src.domain.common.enums import (
    EquipmentType,
    Goal,
    TrainingLevel,
    TrainingStyle,
    WorkoutStyle,
)


@dataclass(slots=True)
class UpdateProfileCommand:
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    training_level: TrainingLevel = TrainingLevel.BEGINNER
    training_style: TrainingStyle = TrainingStyle.BALANCED
    primary_goal: Goal = Goal.GENERAL_HEALTH
    injuries: list[str] = field(default_factory=list)
    notes: str | None = None
    lifestyle_type: str | None = None
    sitting_hours_per_day: float | None = None
    training_history: str | None = None
    months_inactive: int | None = None
    movement_limitations: list[str] = field(default_factory=list)
    pain_areas: list[str] = field(default_factory=list)
    pain_movements: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UpdateEquipmentCommand:
    equipment_types: list[EquipmentType]


@dataclass(slots=True)
class UpdatePreferenceCommand:
    workout_style: WorkoutStyle = WorkoutStyle.BALANCED
