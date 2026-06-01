from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class AIChatCommand:
    user_id: UUID
    workout_id: UUID
    current_workout_plan_exercise_id: UUID | None
    message: str
