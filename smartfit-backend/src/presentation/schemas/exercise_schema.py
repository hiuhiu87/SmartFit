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
    exercise_id: str
    reason: str | None = None
