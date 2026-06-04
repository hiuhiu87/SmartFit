from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TrainingLoadSummary:
    user_id: UUID
    from_date: date_type
    to_date: date_type
    total_volume: float
    total_sets: int
    workout_count: int
    total_duration_minutes: int
    avg_rpe: float | None
    active_energy_burned: float | None
    avg_heart_rate: float | None
    load_score: float
    load_level: str


@dataclass(slots=True)
class MuscleFatigueItem:
    muscle: str
    fatigue_score: float
    last_trained_at: datetime | None
    recent_sets: int
    recent_volume: float
    recovery_status: str


@dataclass(slots=True)
class ExercisePerformanceTrend:
    exercise_id: UUID
    exercise_name: str
    trend: str
    last_weight: float | None
    last_reps: int | None
    best_weight: float | None
    best_reps: int | None
    suggested_next_weight: float | None
    suggested_next_reps: int | None


@dataclass(slots=True)
class TrainingRecommendationContext:
    recent_load: TrainingLoadSummary
    muscle_fatigue: list[MuscleFatigueItem] = field(default_factory=list)
    exercise_trends: list[ExercisePerformanceTrend] = field(default_factory=list)
    suggested_focus: str = "full_body"
    avoid_focus: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(slots=True)
class CompletedWorkout:
    workout_log_id: UUID
    workout_plan_id: UUID
    user_id: UUID
    completed_at: datetime
    duration_minutes: int | None
    total_volume: float
    focus_muscle: str


@dataclass(slots=True)
class SetLogWithExercise:
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    exercise_id: UUID
    exercise_name: str
    primary_muscle: str
    secondary_muscles: list[str]
    completed_at: datetime | None
    set_number: int
    reps_completed: int | None
    weight_kg: float | None
    rpe: int | None
    completed: bool


@dataclass(slots=True)
class WorkoutHealthMetrics:
    workout_log_id: UUID
    completed_at: datetime | None
    duration_minutes: int | None
    active_energy_burned: float | None
    avg_heart_rate: float | None
