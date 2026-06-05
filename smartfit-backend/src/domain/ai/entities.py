from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.common.enums import AIRequestStatus, AIRequestType


@dataclass(slots=True)
class AIRequest:
    id: UUID
    user_id: UUID
    workout_plan_id: UUID | None
    request_type: AIRequestType
    provider: str
    model_name: str
    generation_mode: str | None
    status: AIRequestStatus
    prompt: str | None = None
    response: str | None = None
    input_payload: dict[str, Any] = field(default_factory=dict)
    output_payload: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    fallback_used: bool = False
    latency_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AIUsageDaily:
    user_id: UUID
    date: date_type
    ai_workout_count: int = 0
    ai_chat_count: int = 0
    ai_replacement_count: int = 0
    ai_weekly_report_count: int = 0
    total_ai_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AIUsageLimit:
    ai_workout_limit: int
    ai_chat_limit: int
    ai_replacement_limit: int
    ai_weekly_report_limit: int
    total_ai_limit: int


@dataclass(slots=True)
class AIRequestLog:
    id: UUID | None
    user_id: UUID
    workout_plan_id: UUID | None
    request_type: str
    provider: str
    model_name: str
    generation_mode: str | None = None
    prompt: str | None = None
    response: str | None = None
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    status: str = "success"
    error_code: str | None = None
    error_message: str | None = None
    fallback_used: bool = False
    latency_ms: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class AIChatMessage:
    id: UUID
    ai_request_id: UUID
    role: str
    content: str
    created_at: datetime | None = None


@dataclass(slots=True)
class AIChatHistoryItem:
    id: UUID
    ai_request_id: UUID
    role: str
    message: str
    suggested_action: dict[str, Any] | None = None
    workout_plan_exercise_id: UUID | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class AnalyticsEvent:
    id: UUID
    user_id: UUID
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(slots=True)
class AIAllowedExercise:
    exercise_id: UUID
    name: str
    slug: str
    primary_muscle: str
    equipment: str
    difficulty: str
    movement_type: str | None = None


@dataclass(slots=True)
class AIWorkoutGenerationContext:
    user_id: UUID
    target_date: date_type
    goal: str
    training_level: str
    readiness_score: int
    readiness_category: str
    readiness_recommendation: str
    focus_muscle: str | None
    available_time_minutes: int
    workout_split: str = "full_body"
    equipment: list[str] = field(default_factory=list)
    avoid_exercises: list[str] = field(default_factory=list)
    allowed_exercises: list[AIAllowedExercise] = field(default_factory=list)
    user_note: str | None = None


@dataclass(slots=True)
class AIWorkoutExerciseResult:
    exercise_slug: str
    sets: int
    reps: str
    rest_seconds: int
    rpe: int
    notes: str | None = None


@dataclass(slots=True)
class AIWorkoutGenerationResult:
    workout_title: str
    training_decision: str
    estimated_duration_minutes: int
    exercises: list[AIWorkoutExerciseResult] = field(default_factory=list)
    reasoning_summary: str = ""
    safety_note: str = ""


@dataclass(slots=True)
class AIChatSuggestedAction:
    type: str
    exercise_id: UUID | None = None
    exercise_name: str | None = None
    target_sets: int | None = None
    target_reps: str | None = None
    rest_seconds: int | None = None
    target_rpe: int | None = None
    reason: str | None = None


@dataclass(slots=True)
class AIChatResult:
    reply: str
    intent: str
    suggested_action: AIChatSuggestedAction | None = None


@dataclass(slots=True)
class AIChatContext:
    user_id: UUID
    workout_id: UUID
    current_workout_plan_exercise_id: UUID | None
    user_message: str
    user_profile_summary: dict[str, Any] = field(default_factory=dict)
    readiness_summary: dict[str, Any] | None = None
    workout_summary: dict[str, Any] = field(default_factory=dict)
    current_exercise: dict[str, Any] | None = None
    workout_exercises: list[dict[str, Any]] = field(default_factory=list)
    available_replacements: list[dict[str, Any]] = field(default_factory=list)
