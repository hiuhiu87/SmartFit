from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow


class WorkoutPlanModel(SQLModel, table=True):
    __tablename__ = "workout_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    focus: str = Field(index=True, max_length=50)
    status: str = Field(index=True, max_length=50)
    source: str = Field(index=True, max_length=50)
    readiness_score: float | None = Field(default=None)
    decision: str | None = Field(default=None, max_length=50)
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

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_log_id: UUID = Field(foreign_key="workout_logs.id", index=True)
    workout_plan_exercise_id: UUID = Field(
        foreign_key="workout_plan_exercises.id", index=True
    )
    set_number: int = Field(nullable=False)
    reps_completed: int = Field(nullable=False)
    weight_kg: float | None = Field(default=None)
    rpe: int | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class WorkoutFeedbackModel(SQLModel, table=True):
    __tablename__ = "workout_feedback"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_log_id: UUID = Field(foreign_key="workout_logs.id", index=True)
    difficulty_feedback: str = Field(max_length=50)
    enjoyment_score: int | None = Field(default=None)
    comments: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
