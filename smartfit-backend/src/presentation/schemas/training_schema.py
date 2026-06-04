from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field


class TrainingLoadSummarySchema(BaseModel):
    user_id: str
    from_date: date_type
    to_date: date_type
    total_volume: float
    total_sets: int
    workout_count: int
    total_duration_minutes: int
    avg_rpe: float | None = None
    active_energy_burned: float | None = None
    avg_heart_rate: float | None = None
    load_score: float
    load_level: str


class MuscleFatigueItemSchema(BaseModel):
    muscle: str
    fatigue_score: float
    last_trained_at: datetime | None = None
    recent_sets: int
    recent_volume: float
    recovery_status: str


class ExercisePerformanceTrendSchema(BaseModel):
    exercise_id: str
    exercise_name: str
    trend: str
    last_weight: float | None = None
    last_reps: int | None = None
    best_weight: float | None = None
    best_reps: int | None = None
    suggested_next_weight: float | None = None
    suggested_next_reps: int | None = None


class TrainingRecommendationContextSchema(BaseModel):
    recent_load: TrainingLoadSummarySchema
    muscle_fatigue: list[MuscleFatigueItemSchema] = Field(default_factory=list)
    exercise_trends: list[ExercisePerformanceTrendSchema] = Field(default_factory=list)
    suggested_focus: str
    avoid_focus: list[str] = Field(default_factory=list)
    reason: str
