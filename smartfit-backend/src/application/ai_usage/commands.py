from dataclasses import dataclass
from datetime import date as date_type
from uuid import UUID

from src.domain.ai.entities import AIRequestLog


@dataclass(slots=True)
class CheckAIUsageLimitCommand:
    user_id: UUID
    request_type: str
    target_date: date_type


@dataclass(slots=True)
class RecordAIUsageCommand:
    user_id: UUID
    request_type: str
    target_date: date_type
    request_log: AIRequestLog


@dataclass(slots=True)
class GetAIUsageTodayQuery:
    user_id: UUID
    target_date: date_type
