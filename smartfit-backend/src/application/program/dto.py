from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class ProgramSlotDTO:
    id: UUID
    slot_order: int
    slot_type: str
    movement_patterns: list[str]
    primary_muscles: list[str]
    exercise_roles: list[str]
    required: bool
    base_sets: int
    base_reps: str
    base_rest_seconds: int
    base_rpe: int
    progression_rule: str


@dataclass(slots=True)
class ProgramTemplateDTO:
    id: UUID
    day_index: int
    title: str
    focus_type: str
    workout_type: str
    estimated_duration_minutes: int
    sequence_order: int
    slots: list[ProgramSlotDTO] = field(default_factory=list)


@dataclass(slots=True)
class ProgramPhaseDTO:
    id: UUID
    name: str
    phase_type: str
    start_week: int
    end_week: int
    volume_multiplier: float
    intensity_multiplier: float
    rpe_modifier: int
    is_deload: bool
    notes: str | None = None


@dataclass(slots=True)
class TrainingProgramDTO:
    id: UUID
    name: str
    goal: str
    training_level: str
    training_style: str
    duration_weeks: int
    days_per_week: int
    session_duration_minutes: int
    preferred_split: str
    status: str
    start_date: date
    end_date: date
    current_week: int
    current_day_index: int
    generation_mode: str
    focus_areas: list[str]
    generation_strategy: str = "full_program"
    current_phase: str | None = None
    total_scheduled_workouts: int = 0
    completed_workouts_count: int = 0
    weekly_structure: list[ProgramTemplateDTO] = field(default_factory=list)
    phases: list[ProgramPhaseDTO] = field(default_factory=list)


@dataclass(slots=True)
class TodayProgramWorkoutDTO:
    program_id: UUID
    scheduled: bool
    recommendation: str
    week_number: int | None = None
    day_index: int | None = None
    instance_id: UUID | None = None
    template: ProgramTemplateDTO | None = None
    status: str | None = None
    workout_plan_id: UUID | None = None


@dataclass(slots=True)
class ProgramCalendarDayDTO:
    date: date
    week_number: int
    day_index: int
    title: str
    focus_type: str
    status: str
    workout_plan_id: UUID | None
