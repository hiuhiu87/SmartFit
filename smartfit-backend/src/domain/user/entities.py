from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.common.enums import (
    AuthProvider,
    EquipmentType,
    Goal,
    TrainingLevel,
    TrainingStyle,
    WorkoutStyle,
)


@dataclass(slots=True)
class User:
    id: UUID
    email: str
    password_hash: str | None
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class UserProfile:
    id: UUID
    user_id: UUID
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    training_level: TrainingLevel = TrainingLevel.BEGINNER
    training_style: TrainingStyle = TrainingStyle.BALANCED
    primary_goal: Goal = Goal.GENERAL_HEALTH
    injuries: list[str] = field(default_factory=list)
    notes: str | None = None
    lifestyle_type: str | None = None
    sitting_hours_per_day: float | None = None
    training_history: str | None = None
    months_inactive: int | None = None
    movement_limitations: list[str] = field(default_factory=list)
    pain_areas: list[str] = field(default_factory=list)
    pain_movements: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class UserEquipment:
    id: UUID
    user_id: UUID
    equipment_type: EquipmentType
    created_at: datetime | None = None


@dataclass(slots=True)
class UserPreference:
    id: UUID
    user_id: UUID
    workout_style: WorkoutStyle = WorkoutStyle.BALANCED
    preferred_workout_days: list[str] = field(default_factory=list)
    preferred_session_minutes: int = 45
    dislikes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class NotificationSetting:
    id: UUID
    user_id: UUID
    readiness_push_enabled: bool = True
    workout_reminder_enabled: bool = True
    marketing_enabled: bool = False
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
