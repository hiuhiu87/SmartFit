from dataclasses import dataclass
from datetime import date as date_type
from uuid import UUID


@dataclass(slots=True)
class GetWorkoutDetailQuery:
    user_id: UUID
    workout_id: UUID


@dataclass(slots=True)
class GetWorkoutHistoryQuery:
    user_id: UUID
    limit: int
    offset: int
    status: str | None = None
    from_date: date_type | None = None
    to_date: date_type | None = None
