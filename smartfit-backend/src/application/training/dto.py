from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class TrainingLoadSummaryDTO:
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
class MuscleFatigueItemDTO:
    muscle: str
    fatigue_score: float
    last_trained_at: datetime | None
    recent_sets: int
    recent_volume: float
    recovery_status: str


@dataclass(slots=True)
class ExercisePerformanceTrendDTO:
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
class TrainingRecommendationContextDTO:
    recent_load: TrainingLoadSummaryDTO
    muscle_fatigue: list[MuscleFatigueItemDTO] = field(default_factory=list)
    exercise_trends: list[ExercisePerformanceTrendDTO] = field(default_factory=list)
    suggested_focus: str = "full_body"
    avoid_focus: list[str] = field(default_factory=list)
    reason: str = ""
