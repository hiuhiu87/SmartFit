from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow


class ReadinessScoreModel(SQLModel, table=True):
    __tablename__ = "readiness_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_readiness_scores_user_date"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: date_type = Field(sa_column=Column(Date, nullable=False, index=True))
    score: float = Field(nullable=False)
    category: str = Field(max_length=50)
    recommendation: str = Field(max_length=50)
    confidence: float = Field(nullable=False)
    explanation: str = Field(max_length=2000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
