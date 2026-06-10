from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class UserProfileDTO:
    user_id: UUID
    full_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    training_level: str | None = None
    training_style: str = "balanced"
    primary_goal: str | None = None
    injuries: list[str] = field(default_factory=list)
    notes: str | None = None
    lifestyle_type: str | None = None
    sitting_hours_per_day: float | None = None
    training_history: str | None = None
    months_inactive: int | None = None
    movement_limitations: list[str] = field(default_factory=list)
    pain_areas: list[str] = field(default_factory=list)
    pain_movements: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UserEquipmentDTO:
    user_id: UUID
    equipment_types: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CurrentUserDTO:
    user_id: UUID
    email: str
    is_active: bool
    profile: UserProfileDTO | None = None
    equipment_types: list[str] = field(default_factory=list)
