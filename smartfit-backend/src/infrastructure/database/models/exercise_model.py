from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow

PORTABLE_JSON = JSON().with_variant(JSONB, "postgresql")


class ExerciseModel(SQLModel, table=True):
    __tablename__ = "exercises"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=150)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    muscle_group: str = Field(index=True, max_length=50)
    equipment_type: str = Field(index=True, max_length=50)
    training_level: str = Field(default="beginner", max_length=50)
    secondary_muscles: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    movement_type: str | None = Field(default=None, index=True, max_length=50)
    instruction: str | None = Field(default=None, max_length=4000)
    safety_notes: str | None = Field(default=None, max_length=4000)
    instructions: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    exercise_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", PORTABLE_JSON, nullable=False),
    )
    is_active: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, default=True)
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ExerciseAlternativeModel(SQLModel, table=True):
    __tablename__ = "exercise_alternatives"
    __table_args__ = (
        UniqueConstraint(
            "exercise_id",
            "alternative_exercise_id",
            name="uq_exercise_alternatives_pair",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    exercise_id: UUID = Field(foreign_key="exercises.id", index=True)
    alternative_exercise_id: UUID = Field(foreign_key="exercises.id", index=True)
    reason: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
