from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ProgressionAction(StrEnum):
    INCREASE_WEIGHT = "increase_weight"
    INCREASE_REPS = "increase_reps"
    MAINTAIN = "maintain"
    REDUCE_WEIGHT = "reduce_weight"
    REDUCE_VOLUME = "reduce_volume"
    DELOAD = "deload"
    NO_DATA = "no_data"


@dataclass(slots=True)
class SetPerformance:
    weight: float | None
    reps: int | None
    rpe: int | None
    completed: bool


@dataclass(slots=True)
class ExerciseSessionPerformance:
    workout_log_id: UUID
    completed_at: datetime
    sets: list[SetPerformance] = field(default_factory=list)


@dataclass(slots=True)
class ExercisePerformanceHistory:
    exercise_id: UUID
    exercise_name: str
    recent_sessions: list[ExerciseSessionPerformance] = field(default_factory=list)
    equipment_type: str | None = None
    movement_type: str | None = None


@dataclass(slots=True)
class ProgressionSuggestion:
    exercise_id: UUID
    suggested_weight: float | None
    suggested_sets: int
    suggested_reps: str
    suggested_rpe: int
    action: ProgressionAction
    reason: str
    confidence: float
