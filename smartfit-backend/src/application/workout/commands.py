from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class GenerateWorkoutCommand:
    user_id: UUID
    target_date: date_type
    focus_muscle: str | None
    available_time_minutes: int
    workout_split: str = "full_body"
    generation_mode: str = "auto"
    equipment: list[str] = field(default_factory=list)
    avoid_exercises: list[str] = field(default_factory=list)
    user_note: str | None = None
    goal_override: str | None = None
    training_style_override: str | None = None
    allow_missing_readiness: bool = False


@dataclass(slots=True)
class StartWorkoutCommand:
    user_id: UUID
    workout_id: UUID
    started_at: datetime


@dataclass(slots=True)
class LogWorkoutSetCommand:
    user_id: UUID
    workout_id: UUID
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int
    weight: float | None = None
    reps: int | None = None
    rpe: int | None = None
    completed: bool = True


@dataclass(slots=True)
class SuggestExerciseReplacementCommand:
    user_id: UUID
    workout_id: UUID
    workout_plan_exercise_id: UUID
    reason: str
    available_equipment: list[str] = field(default_factory=list)
    user_note: str | None = None


@dataclass(slots=True)
class ApplyExerciseReplacementCommand:
    user_id: UUID
    workout_id: UUID
    workout_plan_exercise_id: UUID
    replacement_exercise_id: UUID
    target_sets: int
    target_reps: str
    rest_seconds: int
    target_rpe: int | None = None
    reason: str | None = None


@dataclass(slots=True)
class CompleteWorkoutCommand:
    user_id: UUID
    workout_id: UUID
    workout_log_id: UUID
    completed_at: datetime
    duration_minutes: int | None = None
    calories_burned: float | None = None
    avg_heart_rate: float | None = None
    max_heart_rate: float | None = None
    min_heart_rate: float | None = None
    difficulty_feedback: str | None = None
    energy_after: int | None = None
    notes: str | None = None
