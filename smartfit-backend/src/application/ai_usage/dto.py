from dataclasses import dataclass
from datetime import date as date_type


@dataclass(slots=True)
class AIUsageCountsDTO:
    ai_workout_count: int
    ai_chat_count: int
    ai_replacement_count: int
    ai_weekly_report_count: int
    total_ai_count: int


@dataclass(slots=True)
class AIUsageLimitsDTO:
    ai_workout_limit: int
    ai_chat_limit: int
    ai_replacement_limit: int
    ai_weekly_report_limit: int
    total_ai_limit: int


@dataclass(slots=True)
class AIUsageTodayDTO:
    date: date_type
    plan: str
    usage: AIUsageCountsDTO
    limits: AIUsageLimitsDTO
