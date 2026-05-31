from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class UserProfileDTO:
    user_id: UUID
    full_name: str | None = None
    injuries: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UserEquipmentDTO:
    user_id: UUID
    equipment_types: list[str] = field(default_factory=list)
