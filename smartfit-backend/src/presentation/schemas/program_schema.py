from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.presentation.schemas.workout_schema import WorkoutPlanResponseSchema


class ProgramSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreateProgramRequestSchema(ProgramSchema):
    goal: str
    duration_weeks: int = Field(ge=1, le=52)
    days_per_week: int = Field(ge=2, le=6)
    session_duration_minutes: int = Field(ge=20, le=180)
    preferred_split: Literal["full_body", "upper_lower", "push_pull_legs", "custom"] = (
        "upper_lower"
    )
    training_style: Literal[
        "balanced",
        "hypertrophy",
        "strength",
        "conditioning",
        "posture",
        "glute_core",
        "returning",
    ] = "balanced"
    focus_areas: list[str] = Field(default_factory=list)
    generation_mode: Literal["auto", "openrouter", "gemini", "rule_based"] = (
        "rule_based"
    )
    generation_strategy: Literal["structure_only", "full_program"] = "full_program"
    start_date: date | None = None


class ProgramSlotResponseSchema(ProgramSchema):
    id: UUID
    slot_order: int
    slot_type: str
    movement_patterns: list[str]
    primary_muscles: list[str]
    exercise_roles: list[str]
    required: bool
    base_sets: int
    base_reps: str
    base_rest_seconds: int
    base_rpe: int
    progression_rule: str


class ProgramTemplateResponseSchema(ProgramSchema):
    id: UUID
    day_index: int
    title: str
    focus_type: str
    workout_type: str
    estimated_duration_minutes: int
    sequence_order: int
    slots: list[ProgramSlotResponseSchema] = Field(default_factory=list)


class ProgramPhaseResponseSchema(ProgramSchema):
    id: UUID
    name: str
    phase_type: str
    start_week: int
    end_week: int
    volume_multiplier: float
    intensity_multiplier: float
    rpe_modifier: int
    is_deload: bool
    notes: str | None = None


class TrainingProgramResponseSchema(ProgramSchema):
    id: UUID
    name: str
    goal: str
    training_level: str
    training_style: str
    duration_weeks: int
    days_per_week: int
    session_duration_minutes: int
    preferred_split: str
    status: str
    start_date: date
    end_date: date
    current_week: int
    current_day_index: int
    generation_mode: str
    focus_areas: list[str]
    generation_strategy: str = "full_program"
    current_phase: str | None = None
    total_scheduled_workouts: int = 0
    completed_workouts_count: int = 0
    weekly_structure: list[ProgramTemplateResponseSchema] = Field(default_factory=list)
    phases: list[ProgramPhaseResponseSchema] = Field(default_factory=list)


class ScheduledWorkoutSchema(ProgramSchema):
    instance_id: UUID
    title: str
    focus_type: str
    status: str
    planned_workout_plan_id: UUID | None = None


class RecommendationSchema(ProgramSchema):
    action: str
    readiness_adjustment: str
    message: str


class TodayProgramWorkoutResponseSchema(ProgramSchema):
    program_id: UUID
    week_number: int | None = None
    phase: str | None = None
    scheduled_workout: ScheduledWorkoutSchema | None = None
    recommendation: RecommendationSchema | str | None = None

    # Backward compatibility
    scheduled: bool | None = None
    day_index: int | None = None
    instance_id: UUID | None = None
    template: ProgramTemplateResponseSchema | None = None
    status: str | None = None
    workout_plan_id: UUID | None = None


class ProgramCalendarDayResponseSchema(ProgramSchema):
    date: date
    week_number: int
    day_index: int
    title: str
    focus_type: str
    status: str
    workout_plan_id: UUID | None
    planned_workout_plan_id: UUID | None = None


class RescheduleProgramWorkoutRequestSchema(ProgramSchema):
    scheduled_date: date


ProgramWorkoutPlanResponseSchema = WorkoutPlanResponseSchema
