from uuid import UUID

from src.application.user.commands import UpdateEquipmentCommand, UpdateProfileCommand
from src.application.user.dto import UserEquipmentDTO, UserProfileDTO


class GetCurrentUserUseCase:
    async def execute(self, user_id: UUID) -> UserProfileDTO:
        # TODO: load current user aggregate from repositories.
        return UserProfileDTO(user_id=user_id)


class UpdateProfileUseCase:
    async def execute(self, user_id: UUID, command: UpdateProfileCommand) -> UserProfileDTO:
        # TODO: persist profile through user repository.
        return UserProfileDTO(user_id=user_id, full_name=command.full_name, injuries=command.injuries)


class UpdateEquipmentUseCase:
    async def execute(self, user_id: UUID, command: UpdateEquipmentCommand) -> UserEquipmentDTO:
        # TODO: replace user equipment collection through user repository.
        return UserEquipmentDTO(user_id=user_id, equipment_types=[equipment.value for equipment in command.equipment_types])
