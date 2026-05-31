from dataclasses import dataclass
from datetime import date as date_type
from uuid import UUID


@dataclass(slots=True)
class CalculateReadinessCommand:
    user_id: UUID
    date: date_type
