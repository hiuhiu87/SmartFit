from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class ProgressOverviewQuery:
    user_id: UUID


@dataclass(slots=True)
class PersonalRecordsQuery:
    user_id: UUID
