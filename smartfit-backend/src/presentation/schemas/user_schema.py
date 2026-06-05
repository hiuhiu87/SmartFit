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


class EquipmentUpdateRequestSchema(BaseModel):
    equipment_types: list[EquipmentType]
