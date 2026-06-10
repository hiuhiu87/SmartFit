from src.domain.common.enums import EquipmentType, Goal, TrainingLevel, TrainingStyle
from pydantic import BaseModel, Field


class ProfileUpdateRequestSchema(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    age: int | None = Field(default=None, ge=13, le=120)
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    training_level: TrainingLevel = TrainingLevel.BEGINNER
    training_style: TrainingStyle = TrainingStyle.BALANCED
    primary_goal: Goal = Goal.GENERAL_HEALTH
    injuries: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)
    lifestyle_type: str | None = Field(default=None, max_length=100)
    sitting_hours_per_day: float | None = Field(default=None, ge=0, le=24)
    training_history: str | None = Field(default=None, max_length=1000)
    months_inactive: int | None = Field(default=None, ge=0)
    movement_limitations: list[str] = Field(default_factory=list)
    pain_areas: list[str] = Field(default_factory=list)
    pain_movements: list[str] = Field(default_factory=list)


class EquipmentUpdateRequestSchema(BaseModel):
    equipment_types: list[EquipmentType]
