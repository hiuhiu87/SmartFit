from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class HealthSummary:
    id: UUID
    user_id: UUID
    date: date_type
    sleep_hours: float | None = None
    sleep_efficiency: float | None = None
    resting_heart_rate: float | None = None
    heart_rate_variability: float | None = None
    steps: int | None = None
    active_energy_kcal: float | None = None
    source: str = "healthkit"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ManualCheckin:
    id: UUID
    user_id: UUID
    date: date_type
    energy: int
    soreness: int
    stress: int
    motivation: int
    sleep_quality: int
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
