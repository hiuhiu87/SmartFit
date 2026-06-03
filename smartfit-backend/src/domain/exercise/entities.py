from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.domain.common.enums import EquipmentType, MuscleGroup, TrainingLevel


@dataclass(slots=True)
class Exercise:
    id: UUID
    slug: str
    name: str
    description: str | None = None
    muscle_group: MuscleGroup = MuscleGroup.FULL_BODY
    equipment_type: EquipmentType = EquipmentType.BODYWEIGHT
    training_level: TrainingLevel = TrainingLevel.BEGINNER
    secondary_muscles: list[str] = field(default_factory=list)
    movement_type: str | None = None
    movement_pattern: str | None = None
    exercise_role: str | None = None
    fatigue_level: str | None = None
    joint_stress: str | None = None
    substitution_group: str | None = None
    instruction: str | None = None
    safety_notes: str | None = None
    instructions: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ExerciseAlternative:
    id: UUID
    exercise_id: UUID
    alternative_exercise_id: UUID
    reason: str | None = None
    created_at: datetime | None = None
