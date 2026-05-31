from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class ListExercisesQuery:
    primary_muscle: str | None
    equipment: str | None
    difficulty: str | None
    movement_type: str | None
    limit: int
    offset: int


@dataclass(slots=True)
class GetExerciseByIdQuery:
    exercise_id: UUID
