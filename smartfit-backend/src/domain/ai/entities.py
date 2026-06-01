from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.common.enums import AIRequestStatus, AIRequestType


@dataclass(slots=True)
class AIRequest:
    id: UUID
    user_id: UUID
    request_type: AIRequestType
    status: AIRequestStatus
    prompt: str
    response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class AIChatMessage:
    id: UUID
    ai_request_id: UUID
    role: str
    content: str
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
    goal: str
    training_level: str
    readiness_score: int
    readiness_category: str
    readiness_recommendation: str
    focus_muscle: str | None
    available_time_minutes: int
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
