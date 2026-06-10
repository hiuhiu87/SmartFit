from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class CreateProgramCommand:
    user_id: UUID
    goal: str
    duration_weeks: int
    days_per_week: int
    session_duration_minutes: int
    preferred_split: str = "upper_lower"
    training_style: str = "balanced"
    focus_areas: list[str] = field(default_factory=list)
    generation_mode: str = "auto"
    generation_strategy: str = "full_program"
    start_date: date | None = None


@dataclass(slots=True)
class GenerateTodayProgramWorkoutCommand:
    user_id: UUID
    target_date: date


@dataclass(slots=True)
class SkipProgramWorkoutCommand:
    user_id: UUID
    instance_id: UUID


@dataclass(slots=True)
class RescheduleProgramWorkoutCommand:
    user_id: UUID
    instance_id: UUID
    scheduled_date: date
