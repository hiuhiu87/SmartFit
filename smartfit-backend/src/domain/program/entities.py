from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID


class ProgramStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProgramWorkoutStatus(StrEnum):
    SCHEDULED = "scheduled"
    GENERATED = "generated"
    STARTED = "started"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    RESCHEDULED = "rescheduled"


class PreferredSplit(StrEnum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    CUSTOM = "custom"


class ProgramGenerationStrategy(StrEnum):
    STRUCTURE_ONLY = "structure_only"
    FULL_PROGRAM = "full_program"


class ProgramAdjustmentType(StrEnum):
    REDUCED_VOLUME = "reduced_volume"
    RECOVERY_SUBSTITUTION = "recovery_substitution"
    RESCHEDULED = "rescheduled"
    SKIPPED = "skipped"
    EXERCISE_REPLACEMENT = "exercise_replacement"
    DELOAD = "deload"


@dataclass(slots=True)
class ProgramPhase:
    id: UUID
    program_id: UUID
    name: str
    phase_type: str  # foundation, accumulation, intensification, deload, consolidation
    start_week: int
    end_week: int
    volume_multiplier: float
    intensity_multiplier: float
    rpe_modifier: int
    is_deload: bool
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ProgramTemplateSlot:
    id: UUID
    program_workout_template_id: UUID
    slot_order: int
    slot_type: str
    movement_patterns: list[str] = field(default_factory=list)
    primary_muscles: list[str] = field(default_factory=list)
    exercise_roles: list[str] = field(default_factory=list)
    required: bool = True
    base_sets: int = 3
    base_reps: str = "8-12"
    base_rest_seconds: int = 90
    base_rpe: int = 7
    progression_rule: str = "double_progression"


@dataclass(slots=True)
class ProgramWorkoutTemplate:
    id: UUID
    program_id: UUID
    day_index: int
    title: str
    focus_type: str
    workout_type: str
    estimated_duration_minutes: int
    sequence_order: int
    slots: list[ProgramTemplateSlot] = field(default_factory=list)


@dataclass(slots=True)
class ProgramWorkoutInstance:
    id: UUID
    program_id: UUID
    program_workout_template_id: UUID
    user_id: UUID
    scheduled_date: date
    week_number: int
    day_index: int
    planned_workout_plan_id: UUID | None
    actual_workout_plan_id: UUID | None
    adjusted_workout_plan_id: UUID | None = None
    status: ProgramWorkoutStatus = ProgramWorkoutStatus.SCHEDULED
    readiness_adjustment: str | None = None
    adjustment_reason: str | None = None
    original_scheduled_date: date | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ProgramWeek:
    week_number: int
    phase: ProgramPhase | str
    scheduled_workouts: list[ProgramWorkoutInstance] = field(default_factory=list)


@dataclass(slots=True)
class ProgramCalendarDay:
    date: date
    week_number: int
    day_index: int
    title: str
    focus_type: str
    status: str
    workout_plan_id: UUID | None


@dataclass(slots=True)
class TrainingProgram:
    id: UUID
    user_id: UUID
    name: str
    goal: str
    training_level: str
    duration_weeks: int
    days_per_week: int
    session_duration_minutes: int
    preferred_split: PreferredSplit
    status: ProgramStatus
    start_date: date
    end_date: date
    current_week: int = 1
    current_day_index: int = 0
    training_style: str = "balanced"
    generation_mode: str = "rule_based"
    generation_strategy: ProgramGenerationStrategy = ProgramGenerationStrategy.FULL_PROGRAM
    current_phase: str | None = None
    total_scheduled_workouts: int = 0
    completed_workouts_count: int = 0
    focus_areas: list[str] = field(default_factory=list)
    templates: list[ProgramWorkoutTemplate] = field(default_factory=list)
    phases: list[ProgramPhase] = field(default_factory=list)
    instances: list[ProgramWorkoutInstance] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
