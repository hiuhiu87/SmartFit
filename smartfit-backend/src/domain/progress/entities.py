from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class LatestCompletedWorkout:
    workout_id: UUID
    workout_log_id: UUID
    title: str
    completed_at: datetime
    duration_minutes: int | None
    total_volume: float
    focus_muscle: str


@dataclass(slots=True)
class MuscleDistributionItem:
    muscle: str
    workout_count: int
    set_count: int
    volume: float
    percentage: int = 0


@dataclass(slots=True)
class ProgressOverview:
    from_date: date_type
    to_date: date_type
    weekly_workouts_completed: int
    weekly_workout_target: int
    consistency_percentage: int
    total_volume: float
    average_readiness: float | None
    completed_workout_days: list[date_type] = field(default_factory=list)
    latest_completed_workout: LatestCompletedWorkout | None = None
    muscle_distribution: list[MuscleDistributionItem] = field(default_factory=list)


@dataclass(slots=True)
class PersonalRecord:
    exercise_id: UUID
    exercise_name: str
    primary_muscle: str
    best_weight: float
    best_reps: int
    best_set_volume: float
    estimated_1rm: float
    workout_id: UUID
    workout_log_id: UUID
    achieved_at: datetime
