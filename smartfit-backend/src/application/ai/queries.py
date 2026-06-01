from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GetAIChatHistoryQuery:
    user_id: UUID
    workout_id: UUID
    limit: int = 50
    offset: int = 0
