from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class WorkoutPlanDTO:
    workout_id: UUID
    title: str
    status: str
    exercises: list[dict[str, str | int]] = field(default_factory=list)
