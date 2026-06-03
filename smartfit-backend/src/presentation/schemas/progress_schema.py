from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field


class MuscleDistributionItemSchema(BaseModel):
    muscle: str
    workout_count: int
    set_count: int
    volume: float
    percentage: int


class LatestCompletedWorkoutSchema(BaseModel):
    workout_id: str
    workout_log_id: str
    title: str
    completed_at: datetime
    duration_minutes: int | None = None
    total_volume: float
    focus_muscle: str


class ProgressOverviewResponseSchema(BaseModel):
    from_date: date_type
    to_date: date_type
    weekly_workouts_completed: int
    weekly_workout_target: int
    consistency_percentage: int
    total_volume_this_week: float
    average_readiness_this_week: float | None = None
    completed_workout_days: list[date_type] = Field(default_factory=list)
    latest_completed_workout: LatestCompletedWorkoutSchema | None = None
    muscle_distribution: list[MuscleDistributionItemSchema] = Field(
        default_factory=list
    )


class PersonalRecordResponseSchema(BaseModel):
    exercise_id: str
    exercise_name: str
    primary_muscle: str
    best_weight: float
    best_reps: int
    best_set_volume: float
    estimated_1rm: float
    workout_id: str
    workout_log_id: str
    achieved_at: datetime


class PersonalRecordsResponseSchema(BaseModel):
    items: list[PersonalRecordResponseSchema] = Field(default_factory=list)
    limit: int
    total: int


class WeeklyReportResponseSchema(BaseModel):
    week_start: date_type
    week_end: date_type
    summary: str
    highlights: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    overview: ProgressOverviewResponseSchema
