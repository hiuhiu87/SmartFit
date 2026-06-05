from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class WorkoutSetLogDTO:
    set_log_id: UUID
    set_number: int
    weight: float | None
    reps: int | None
    rpe: int | None
    completed: bool


@dataclass(slots=True)
class WorkoutExerciseDTO:
    workout_plan_exercise_id: UUID
    exercise_id: UUID
    name: str
    order_index: int
    primary_muscle: str
    equipment: str
    target_sets: int
    target_reps: str
    target_weight: float | None
    rest_seconds: int | None
    target_rpe: int
    notes: str | None = None
    logged_sets: list[WorkoutSetLogDTO] = field(default_factory=list)


@dataclass(slots=True)
class WorkoutPlanDTO:
    workout_id: UUID
    workout_log_id: UUID | None = None
    title: str = ""
    goal: str = ""
    focus_muscle: str = ""
    estimated_duration_minutes: int | None = None
    training_decision: str | None = None
    ai_reasoning_summary: str | None = None
    safety_note: str | None = None
    status: str = ""
    source: str = ""
    exercises: list[WorkoutExerciseDTO] = field(default_factory=list)


@dataclass(slots=True)
class StartWorkoutDTO:
    workout_id: UUID
    workout_log_id: UUID
    status: str
    started_at: datetime | None


@dataclass(slots=True)
class SetLogDTO:
    set_log_id: UUID
    workout_log_id: UUID
    workout_plan_exercise_id: UUID
    set_number: int


@dataclass(slots=True)
class ReplacementCurrentExerciseDTO:
    exercise_id: UUID
    name: str
    primary_muscle: str
    equipment: str


@dataclass(slots=True)
class ReplacementOptionDTO:
    exercise_id: UUID
    name: str
    primary_muscle: str
    equipment: str
    difficulty: str | None
    target_sets: int
    target_reps: str
    rest_seconds: int
    target_rpe: int | None
    reason: str
    safety_note: str | None = None


@dataclass(slots=True)
class SuggestExerciseReplacementDTO:
    current_exercise: ReplacementCurrentExerciseDTO
    replacement_options: list[ReplacementOptionDTO] = field(default_factory=list)
    safety_note: str | None = None


@dataclass(slots=True)
class ApplyExerciseReplacementDTO:
    workout_id: UUID
    workout_plan_exercise_id: UUID
    replaced_exercise_id: UUID
    replacement_exercise_id: UUID
    name: str
    primary_muscle: str
    equipment: str
    target_sets: int
    target_reps: str
    rest_seconds: int
    target_rpe: int | None
    is_replacement: bool = True


@dataclass(slots=True)
class CompleteWorkoutDTO:
    workout_id: UUID
    workout_log_id: UUID
    status: str
    total_volume: float
    completed_at: datetime | None


@dataclass(slots=True)
class WorkoutHistoryItemDTO:
    workout_id: UUID
    workout_log_id: UUID | None
    title: str
    date: date_type
    status: str
    duration_minutes: int | None
    total_volume: float
    difficulty_feedback: str | None
    focus_muscle: str
    training_decision: str | None
    source: str


@dataclass(slots=True)
class WorkoutHistoryDTO:
    items: list[WorkoutHistoryItemDTO] = field(default_factory=list)
    limit: int = 20
    offset: int = 0
    total: int = 0
