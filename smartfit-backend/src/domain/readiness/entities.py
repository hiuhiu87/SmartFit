from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from uuid import UUID

from src.domain.common.enums import ReadinessCategory, ReadinessRecommendation


@dataclass(slots=True)
class ReadinessScore:
    id: UUID
    user_id: UUID
    date: date_type
    score: float
    category: ReadinessCategory
    recommendation: ReadinessRecommendation
    confidence: float
    explanation: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
