from uuid import UUID

from pydantic import BaseModel, Field


class ExerciseResponseSchema(BaseModel):
    id: str
    name: str
    slug: str
    primary_muscle: str
    secondary_muscles: list[str] = Field(default_factory=list)
    equipment: str
    difficulty: str
    movement_type: str | None = None
    instruction: str | None = None
    safety_notes: str | None = None


class ExerciseListDataSchema(BaseModel):
    items: list[ExerciseResponseSchema] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class ExerciseListResponseSchema(ExerciseListDataSchema):
    pass


class ReplaceExerciseRequestSchema(BaseModel):
    workout_id: UUID
    workout_plan_exercise_id: UUID
    reason: str = Field(default="equipment_unavailable", max_length=100)
    available_equipment: list[str] = Field(default_factory=list)
    user_note: str | None = Field(default=None, max_length=1000)


class ReplacementCurrentExerciseSchema(BaseModel):
    exercise_id: str
    name: str
    primary_muscle: str
    equipment: str


class ReplacementOptionSchema(BaseModel):
    exercise_id: str
    name: str
    primary_muscle: str
    equipment: str
    difficulty: str | None = None
    target_sets: int
    target_reps: str
    rest_seconds: int
    target_rpe: int | None = None
    reason: str
    safety_note: str | None = None


class ReplaceExerciseResponseSchema(BaseModel):
    current_exercise: ReplacementCurrentExerciseSchema
    replacement_options: list[ReplacementOptionSchema] = Field(default_factory=list)
    safety_note: str | None = None
