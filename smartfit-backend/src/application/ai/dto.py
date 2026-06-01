from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class AIChatSuggestedActionDTO:
    type: str
    exercise_id: UUID | None = None
    exercise_name: str | None = None
    target_sets: int | None = None
    target_reps: str | None = None
    rest_seconds: int | None = None
    target_rpe: int | None = None
    reason: str | None = None


@dataclass(slots=True)
class AIChatResponseDTO:
    reply: str
    intent: str
    suggested_action: AIChatSuggestedActionDTO | None = None


@dataclass(slots=True)
class AIChatHistoryItemDTO:
    id: UUID
    role: str
    message: str
    suggested_action: AIChatSuggestedActionDTO | None = None
    workout_plan_exercise_id: UUID | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class AIChatHistoryDTO:
    items: list[AIChatHistoryItemDTO]
    limit: int
    offset: int
    total: int
