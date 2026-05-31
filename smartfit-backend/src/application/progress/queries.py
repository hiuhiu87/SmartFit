from dataclasses import dataclass
from datetime import date as date_type
from uuid import UUID


@dataclass(slots=True)
class GetProgressOverviewQuery:
    user_id: UUID
    from_date: date_type | None = None
    to_date: date_type | None = None


@dataclass(slots=True)
class GetPersonalRecordsQuery:
    user_id: UUID
    limit: int = 20
    exercise_id: UUID | None = None
    metric: str | None = None


@dataclass(slots=True)
class GetWeeklyReportQuery:
    user_id: UUID
    week_start: date_type | None = None
