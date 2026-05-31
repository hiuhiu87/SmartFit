from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow


class AIRequestModel(SQLModel, table=True):
    __tablename__ = "ai_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    request_type: str = Field(index=True, max_length=50)
    status: str = Field(index=True, max_length=50)
    prompt: str = Field(max_length=4000)
    response: str | None = Field(default=None, max_length=12000)
    request_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB, nullable=False),
    )
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class AIChatMessageModel(SQLModel, table=True):
    __tablename__ = "ai_chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ai_request_id: UUID = Field(foreign_key="ai_requests.id", index=True)
    role: str = Field(max_length=50)
    content: str = Field(max_length=4000)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))


class AnalyticsEventModel(SQLModel, table=True):
    __tablename__ = "analytics_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    event_name: str = Field(index=True, max_length=100)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
