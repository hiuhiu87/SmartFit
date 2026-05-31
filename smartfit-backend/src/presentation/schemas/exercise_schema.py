from pydantic import BaseModel


class ExerciseResponseSchema(BaseModel):
    id: str
    slug: str
    name: str
    muscle_group: str
    equipment_type: str


class ReplaceExerciseRequestSchema(BaseModel):
    exercise_id: str
    reason: str | None = None
