from dataclasses import dataclass
from uuid import UUID

from src.domain.common.enums import MuscleGroup


@dataclass(slots=True)
class GenerateWorkoutCommand:
    user_id: UUID
    focus: MuscleGroup
    duration_minutes: int = 45


@dataclass(slots=True)
class StartWorkoutCommand:
    workout_id: UUID


@dataclass(slots=True)
class LogSetCommand:
    workout_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int
    reps_completed: int
    weight_kg: float | None = None
    rpe: int | None = None


@dataclass(slots=True)
class CompleteWorkoutCommand:
    workout_id: UUID
    duration_minutes: int
    notes: str | None = None
