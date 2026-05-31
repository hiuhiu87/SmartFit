from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.domain.common.enums import (
    DifficultyFeedback,
    MuscleGroup,
    WorkoutSource,
    WorkoutStatus,
)


@dataclass(slots=True)
class WorkoutPlanExercise:
    id: UUID
    workout_plan_id: UUID
    exercise_id: UUID
    order_index: int
    target_sets: int
    target_reps: str
    target_rpe: int
    notes: str | None = None


@dataclass(slots=True)
class WorkoutPlan:
    id: UUID
    user_id: UUID
    title: str
    focus: MuscleGroup
    status: WorkoutStatus
    source: WorkoutSource
    readiness_score: float | None = None
    decision: str | None = None
    exercises: list[WorkoutPlanExercise] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutSetLog:
    id: UUID
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int
    reps_completed: int
    weight_kg: float | None = None
    rpe: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class WorkoutLog:
    id: UUID
    workout_plan_id: UUID
    user_id: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int | None = None
    notes: str | None = None
    sets: list[WorkoutSetLog] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutFeedback:
    id: UUID
    workout_log_id: UUID
    difficulty_feedback: DifficultyFeedback
    enjoyment_score: int | None = None
    comments: str | None = None
    created_at: datetime | None = None
