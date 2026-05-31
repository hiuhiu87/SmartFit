from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow


class HealthSummaryModel(SQLModel, table=True):
    __tablename__ = "health_summaries"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_health_summaries_user_date"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: date_type = Field(sa_column=Column(Date, nullable=False, index=True))
    sleep_hours: float | None = Field(default=None)
    sleep_efficiency: float | None = Field(default=None)
    resting_heart_rate: float | None = Field(default=None)
    heart_rate_variability: float | None = Field(default=None)
    steps: int | None = Field(default=None)
    active_energy_kcal: float | None = Field(default=None)
    source: str = Field(default="healthkit", max_length=50)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class ManualCheckinModel(SQLModel, table=True):
    __tablename__ = "manual_checkins"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_manual_checkins_user_date"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: date_type = Field(sa_column=Column(Date, nullable=False, index=True))
    energy: int = Field(nullable=False)
    soreness: int = Field(nullable=False)
    stress: int = Field(nullable=False)
    motivation: int = Field(nullable=False)
    sleep_quality: int = Field(nullable=False)
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
