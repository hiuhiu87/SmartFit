from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow


class WorkoutPlanModel(SQLModel, table=True):
    __tablename__ = "workout_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    target_date: date_type = Field(sa_column=Column(Date, nullable=False, index=True))
    title: str = Field(max_length=255)
    goal: str = Field(index=True, max_length=50)
    focus: str = Field(index=True, max_length=50)
    status: str = Field(index=True, max_length=50)
    source: str = Field(index=True, max_length=50)
    estimated_duration_minutes: int | None = Field(default=None)
    readiness_score: float | None = Field(default=None)
    decision: str | None = Field(default=None, max_length=50)
    ai_reasoning_summary: str | None = Field(default=None, max_length=2000)
    safety_note: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class WorkoutPlanExerciseModel(SQLModel, table=True):
    __tablename__ = "workout_plan_exercises"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_plan_id: UUID = Field(foreign_key="workout_plans.id", index=True)
    exercise_id: UUID = Field(foreign_key="exercises.id", index=True)
    order_index: int = Field(nullable=False)
    target_sets: int = Field(nullable=False)
    target_reps: str = Field(max_length=50)
    target_rpe: int = Field(nullable=False)
    target_weight: float | None = Field(default=None)
    rest_seconds: int | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1000)


class WorkoutLogModel(SQLModel, table=True):
    __tablename__ = "workout_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_plan_id: UUID = Field(foreign_key="workout_plans.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    duration_minutes: int | None = Field(default=None)
    total_volume: float = Field(default=0)
    calories_burned: float | None = Field(default=None)
    avg_heart_rate: float | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class WorkoutSetLogModel(SQLModel, table=True):
    __tablename__ = "workout_set_logs"
    __table_args__ = (
        UniqueConstraint(
            "workout_log_id",
            "workout_plan_exercise_id",
            "set_number",
            name="uq_workout_set_logs_log_exercise_set",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_log_id: UUID = Field(foreign_key="workout_logs.id", index=True)
    workout_plan_exercise_id: UUID = Field(
        foreign_key="workout_plan_exercises.id", index=True
    )
    set_number: int = Field(nullable=False)
    reps_completed: int | None = Field(default=None)
    weight_kg: float | None = Field(default=None)
    rpe: int | None = Field(default=None)
    completed: bool = Field(
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


class WorkoutFeedbackModel(SQLModel, table=True):
    __tablename__ = "workout_feedback"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_log_id: UUID = Field(foreign_key="workout_logs.id", index=True)
    difficulty_feedback: str | None = Field(default=None, max_length=50)
    energy_after: int | None = Field(default=None)
    enjoyment_score: int | None = Field(default=None)
    comments: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
