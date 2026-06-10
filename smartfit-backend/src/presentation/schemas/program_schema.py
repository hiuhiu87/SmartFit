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
    weekly_structure: list[ProgramTemplateResponseSchema] = Field(default_factory=list)


class TodayProgramWorkoutResponseSchema(ProgramSchema):
    program_id: UUID
    scheduled: bool
    recommendation: str
    week_number: int | None = None
    day_index: int | None = None
    instance_id: UUID | None = None
    template: ProgramTemplateResponseSchema | None = None
    status: str | None = None
    workout_plan_id: UUID | None = None


class RescheduleProgramWorkoutRequestSchema(ProgramSchema):
    scheduled_date: date


ProgramWorkoutPlanResponseSchema = WorkoutPlanResponseSchema
