from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from src.domain.common.enums import (
    DifficultyFeedback,
    Goal,
    MuscleGroup,
    WorkoutSource,
    WorkoutStatus,
)
from src.domain.common.exceptions import InvalidWorkoutStateError


@dataclass(slots=True)
class WorkoutSetLog:
    id: UUID
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int
    reps_completed: int | None = None
    weight_kg: float | None = None
    rpe: int | None = None
    completed: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutPlanExercise:
    id: UUID
    workout_plan_id: UUID
    exercise_id: UUID
    order_index: int
    target_sets: int
    target_reps: str
    target_rpe: int
    target_weight: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    name: str | None = None
    primary_muscle: str | None = None
    equipment: str | None = None
    logged_sets: list[WorkoutSetLog] = field(default_factory=list)


@dataclass(slots=True)
class WorkoutPlan:
    id: UUID
    user_id: UUID
    target_date: date_type
    title: str
    goal: Goal
    focus: MuscleGroup
    status: WorkoutStatus
    source: WorkoutSource
    estimated_duration_minutes: int | None = None
    readiness_score: float | None = None
    decision: str | None = None
    ai_reasoning_summary: str | None = None
    safety_note: str | None = None
    workout_log_id: UUID | None = None
    exercises: list[WorkoutPlanExercise] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def start(self) -> None:
        if self.status == WorkoutStatus.STARTED:
            return
        if self.status != WorkoutStatus.GENERATED:
            raise InvalidWorkoutStateError(
                f"Workout cannot be started from status '{self.status.value}'."
            )
        self.status = WorkoutStatus.STARTED

    def complete(self) -> None:
        if self.status == WorkoutStatus.COMPLETED:
            return
        if self.status != WorkoutStatus.STARTED:
            raise InvalidWorkoutStateError(
                f"Workout cannot be completed from status '{self.status.value}'."
            )
        self.status = WorkoutStatus.COMPLETED


@dataclass(slots=True)
class WorkoutLog:
    id: UUID
    workout_plan_id: UUID
    user_id: UUID
    title: str | None = None
    focus_muscle: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int | None = None
    total_volume: float = 0
    calories_burned: float | None = None
    avg_heart_rate: float | None = None
    notes: str | None = None
    sets: list[WorkoutSetLog] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutFeedback:
    id: UUID
    workout_log_id: UUID
    difficulty_feedback: DifficultyFeedback | None = None
    energy_after: int | None = None
    comments: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class WorkoutHistoryItem:
    workout_id: UUID
    workout_log_id: UUID | None
    title: str
    date: date_type
    status: str
    duration_minutes: int | None
    total_volume: float
    difficulty_feedback: str | None
    focus_muscle: str
    training_decision: str | None
    source: str
