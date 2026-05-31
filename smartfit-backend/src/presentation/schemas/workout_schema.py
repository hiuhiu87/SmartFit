from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class GenerateWorkoutRequestSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: date_type = Field(default_factory=date_type.today)
    focus_muscle: str | None = Field(
        default=None, validation_alias=AliasChoices("focus_muscle", "focus")
    )
    available_time_minutes: int = Field(
        ge=10,
        le=180,
        validation_alias=AliasChoices("available_time_minutes", "available_minutes"),
    )
    equipment: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("equipment", "equipment_types"),
    )
    avoid_exercises: list[str] = Field(default_factory=list)
    user_note: str | None = Field(default=None, max_length=2000)


class LoggedSetResponseSchema(BaseModel):
    set_log_id: str
    set_number: int
    weight: float | None = None
    reps: int | None = None
    rpe: int | None = None
    completed: bool


class WorkoutExerciseResponseSchema(BaseModel):
    workout_plan_exercise_id: str
    exercise_id: str
    name: str
    order_index: int
    primary_muscle: str
    equipment: str
    target_sets: int
    target_reps: str
    target_weight: float | None = None
    rest_seconds: int | None = None
    target_rpe: int
    notes: str | None = None
    logged_sets: list[LoggedSetResponseSchema] = Field(default_factory=list)


class WorkoutPlanResponseSchema(BaseModel):
    workout_id: str
    workout_log_id: str | None = None
    title: str
    goal: str
    focus_muscle: str
    estimated_duration_minutes: int | None = None
    training_decision: str | None = None
    ai_reasoning_summary: str | None = None
    safety_note: str | None = None
    status: str
    source: str
    exercises: list[WorkoutExerciseResponseSchema] = Field(default_factory=list)


class WorkoutDetailResponseSchema(WorkoutPlanResponseSchema):
    pass


class StartWorkoutRequestSchema(BaseModel):
    started_at: datetime | None = None


class StartWorkoutResponseSchema(BaseModel):
    workout_id: str
    workout_log_id: str
    status: str
    started_at: datetime | None = None


class LogSetRequestSchema(BaseModel):
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int = Field(ge=1)
    weight: float | None = Field(default=None, ge=0)
    reps: int | None = Field(default=None, ge=0)
    rpe: int | None = Field(default=None, ge=1, le=10)
    completed: bool = True


class LogSetResponseSchema(BaseModel):
    set_log_id: str
    workout_log_id: str
    workout_plan_exercise_id: str
    set_number: int


class CompleteWorkoutRequestSchema(BaseModel):
    workout_log_id: UUID
    completed_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=300)
    calories_burned: float | None = Field(default=None, ge=0)
    avg_heart_rate: float | None = Field(default=None, ge=0)
    difficulty_feedback: str | None = None
    energy_after: int | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=2000)


class CompleteWorkoutResponseSchema(BaseModel):
    workout_id: str
    workout_log_id: str
    status: str
    total_volume: float
    completed_at: datetime | None = None


class WorkoutHistoryItemSchema(BaseModel):
    workout_id: str
    workout_log_id: str | None = None
    title: str
    date: date_type
    status: str
    duration_minutes: int | None = None
    total_volume: float
    difficulty_feedback: str | None = None
    focus_muscle: str
    training_decision: str | None = None
    source: str


class WorkoutHistoryResponseSchema(BaseModel):
    items: list[WorkoutHistoryItemSchema] = Field(default_factory=list)
    limit: int
    offset: int
    total: int
