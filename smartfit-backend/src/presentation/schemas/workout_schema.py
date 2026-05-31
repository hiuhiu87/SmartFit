from uuid import UUID

from src.domain.common.enums import MuscleGroup
from pydantic import BaseModel, Field


class GenerateWorkoutRequestSchema(BaseModel):
    focus: MuscleGroup
    duration_minutes: int = Field(default=45, ge=10, le=180)


class StartWorkoutRequestSchema(BaseModel):
    started: bool = True


class LogSetRequestSchema(BaseModel):
    workout_plan_exercise_id: UUID
    set_number: int = Field(ge=1)
    reps_completed: int = Field(ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    rpe: int | None = Field(default=None, ge=1, le=10)


class CompleteWorkoutRequestSchema(BaseModel):
    duration_minutes: int = Field(ge=1, le=300)
    notes: str | None = Field(default=None, max_length=2000)
