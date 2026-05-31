from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class ExerciseDTO:
    id: UUID
    name: str
    slug: str
    primary_muscle: str
    secondary_muscles: list[str] = field(default_factory=list)
    equipment: str = ""
    difficulty: str = ""
    movement_type: str | None = None
    instruction: str | None = None
    safety_notes: str | None = None


@dataclass(slots=True)
class ExerciseListDTO:
    items: list[ExerciseDTO] = field(default_factory=list)
    limit: int = 20
    offset: int = 0
    total: int = 0
