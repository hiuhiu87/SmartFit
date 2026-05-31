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
    instructions: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ExerciseAlternative:
    id: UUID
    exercise_id: UUID
    alternative_exercise_id: UUID
    reason: str | None = None
    created_at: datetime | None = None
