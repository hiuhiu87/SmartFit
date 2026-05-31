from datetime import date as date_type

from pydantic import BaseModel, Field


class HealthSummaryRequestSchema(BaseModel):
    date: date_type
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_efficiency: float | None = Field(default=None, ge=0, le=100)
    resting_heart_rate: float | None = Field(default=None, ge=20, le=220)
    heart_rate_variability: float | None = Field(default=None, ge=0)
    steps: int | None = Field(default=None, ge=0)
    active_energy_kcal: float | None = Field(default=None, ge=0)


class ManualCheckinRequestSchema(BaseModel):
    date: date_type
    energy: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    motivation: int = Field(ge=1, le=5)
    sleep_quality: int = Field(ge=1, le=5)
    notes: str | None = Field(default=None, max_length=2000)
