from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Date, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from src.infrastructure.database.base import utcnow

PORTABLE_JSON = JSON().with_variant(JSONB, "postgresql")


class TrainingProgramModel(SQLModel, table=True):
    __tablename__ = "training_programs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    goal: str = Field(index=True, max_length=50)
    training_level: str = Field(max_length=50)
    training_style: str = Field(default="balanced", max_length=50)
    duration_weeks: int
    days_per_week: int
    session_duration_minutes: int
    preferred_split: str = Field(max_length=50)
    status: str = Field(index=True, max_length=50)
    start_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    end_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    current_week: int = 1
    current_day_index: int = 0
    generation_mode: str = Field(default="rule_based", max_length=50)
    generation_strategy: str = Field(default="full_program", max_length=50)
    current_phase: str | None = Field(default=None, max_length=50)
    total_scheduled_workouts: int = Field(default=0)
    completed_workouts_count: int = Field(default=0)
    focus_areas: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProgramPhaseModel(SQLModel, table=True):
    __tablename__ = "program_phases"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_id: UUID = Field(foreign_key="training_programs.id", index=True)
    name: str = Field(max_length=255)
    phase_type: str = Field(max_length=50)
    start_week: int
    end_week: int
    volume_multiplier: float
    intensity_multiplier: float
    rpe_modifier: int
    is_deload: bool = False
    notes: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProgramWorkoutTemplateModel(SQLModel, table=True):
    __tablename__ = "program_workout_templates"
    __table_args__ = (
        UniqueConstraint(
            "program_id", "day_index", name="uq_program_workout_templates_day"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_id: UUID = Field(foreign_key="training_programs.id", index=True)
    day_index: int
    title: str = Field(max_length=255)
    focus_type: str = Field(max_length=50)
    workout_type: str = Field(max_length=50)
    estimated_duration_minutes: int
    sequence_order: int


class ProgramTemplateSlotModel(SQLModel, table=True):
    __tablename__ = "program_template_slots"
    __table_args__ = (
        UniqueConstraint(
            "program_workout_template_id",
            "slot_order",
            name="uq_program_template_slots_order",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_workout_template_id: UUID = Field(
        foreign_key="program_workout_templates.id", index=True
    )
    slot_order: int
    slot_type: str = Field(max_length=50)
    movement_patterns: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    primary_muscles: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    exercise_roles: list[str] = Field(
        default_factory=list, sa_column=Column(PORTABLE_JSON, nullable=False)
    )
    required: bool = True
    base_sets: int
    base_reps: str = Field(max_length=50)
    base_rest_seconds: int
    base_rpe: int
    progression_rule: str = Field(max_length=100)


class ProgramWorkoutInstanceModel(SQLModel, table=True):
    __tablename__ = "program_workout_instances"
    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "week_number",
            "day_index",
            name="uq_program_workout_instances_position",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_id: UUID = Field(foreign_key="training_programs.id", index=True)
    program_workout_template_id: UUID = Field(
        foreign_key="program_workout_templates.id", index=True
    )
    user_id: UUID = Field(foreign_key="users.id", index=True)
    scheduled_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    week_number: int
    day_index: int
    planned_workout_plan_id: UUID | None = Field(
        default=None, foreign_key="workout_plans.id", index=True
    )
    actual_workout_plan_id: UUID | None = Field(
        default=None, foreign_key="workout_plans.id", index=True
    )
    adjusted_workout_plan_id: UUID | None = Field(
        default=None, foreign_key="workout_plans.id", index=True
    )
    status: str = Field(index=True, max_length=50)
    readiness_adjustment: str | None = Field(default=None, max_length=50)
    adjustment_reason: str | None = Field(default=None, max_length=255)
    original_scheduled_date: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
