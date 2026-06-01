from datetime import date as date_type
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow

PORTABLE_JSON = JSON().with_variant(JSONB, "postgresql")


class AIRequestModel(SQLModel, table=True):
    __tablename__ = "ai_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    workout_plan_id: UUID | None = Field(
        default=None, foreign_key="workout_plans.id", index=True
    )
    request_type: str = Field(index=True, max_length=50)
    provider: str = Field(default="gemini", max_length=50)
    model_name: str = Field(default="", max_length=100)
    generation_mode: str | None = Field(default=None, max_length=50)
    status: str = Field(index=True, max_length=50)
    prompt: str | None = Field(default=None, max_length=4000)
    response: str | None = Field(default=None, max_length=12000)
    input_payload: dict = Field(
        default_factory=dict, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    output_payload: dict = Field(
        default_factory=dict, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None, max_length=4000)
    fallback_used: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False, default=False)
    )
    latency_ms: int | None = Field(default=None)
    request_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", PORTABLE_JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AIUsageDailyModel(SQLModel, table=True):
    __tablename__ = "ai_usage_daily"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_ai_usage_daily_user_date"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    date: date_type = Field(sa_column=Column(Date, nullable=False, index=True))
    ai_workout_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    ai_chat_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    ai_replacement_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    ai_weekly_report_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    total_ai_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AIChatMessageModel(SQLModel, table=True):
    __tablename__ = "ai_chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ai_request_id: UUID = Field(foreign_key="ai_requests.id", index=True)
    role: str = Field(max_length=50)
    content: str = Field(max_length=4000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class AnalyticsEventModel(SQLModel, table=True):
    __tablename__ = "analytics_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    event_name: str = Field(index=True, max_length=100)
    payload: dict = Field(
        default_factory=dict, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
