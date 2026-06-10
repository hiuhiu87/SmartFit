from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel

from src.domain.common.enums import AuthProvider
from src.infrastructure.database.base import utcnow

POSTGRES_STRING_ARRAY = JSON().with_variant(ARRAY(Text()), "postgresql")


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str | None = Field(default=None, max_length=255)
    auth_provider: str = Field(default=AuthProvider.EMAIL.value, max_length=50)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserProfileModel(SQLModel, table=True):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    full_name: str | None = Field(default=None, max_length=255)
    age: int | None = Field(default=None)
    height_cm: float | None = Field(default=None)
    weight_kg: float | None = Field(default=None)
    training_level: str = Field(default="beginner", max_length=50)
    training_style: str = Field(default="balanced", max_length=50)
    primary_goal: str = Field(default="general_health", max_length=50)
    injuries: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    notes: str | None = Field(default=None, max_length=2000)
    lifestyle_type: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    sitting_hours_per_day: float | None = Field(default=None)
    training_history: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    months_inactive: int | None = Field(default=None)
    movement_limitations: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    pain_areas: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    pain_movements: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserEquipmentModel(SQLModel, table=True):
    __tablename__ = "user_equipment"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "equipment_type", name="uq_user_equipment_user_equipment_type"
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    equipment_type: str = Field(index=True, max_length=50)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserPreferenceModel(SQLModel, table=True):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preferences_user_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    workout_style: str = Field(default="balanced", max_length=50)
    preferred_workout_days: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    preferred_session_minutes: int = Field(default=45)
    dislikes: list[str] = Field(
        default_factory=list, sa_column=Column(POSTGRES_STRING_ARRAY, nullable=False)
    )
    preference_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class NotificationSettingModel(SQLModel, table=True):
    __tablename__ = "notification_settings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_settings_user_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    readiness_push_enabled: bool = Field(default=True)
    workout_reminder_enabled: bool = Field(default=True)
    marketing_enabled: bool = Field(default=False)
    quiet_hours_start: str | None = Field(default=None, max_length=5)
    quiet_hours_end: str | None = Field(default=None, max_length=5)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
