from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from src.application.user.commands import UpdateEquipmentCommand, UpdateProfileCommand
from src.application.user.dto import CurrentUserDTO, UserEquipmentDTO, UserProfileDTO
from src.domain.user.entities import UserEquipment, UserProfile
from src.domain.common.exceptions import NotFoundError
from src.domain.common.exceptions import ValidationError
from src.domain.user.repositories import UserRepository


class GetCurrentUserProfileUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(self, user_id: UUID) -> CurrentUserDTO:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        profile = await self.user_repository.get_profile(user_id)
        equipment = await self.user_repository.list_equipment(user_id)
        profile_dto = None
        if profile is not None:
            profile_dto = UserProfileDTO(
                user_id=profile.user_id,
                full_name=profile.full_name,
                age=profile.age,
                height_cm=profile.height_cm,
                weight_kg=profile.weight_kg,
                training_level=profile.training_level.value,
                primary_goal=profile.primary_goal.value,
                injuries=profile.injuries,
                notes=profile.notes,
            )
        return CurrentUserDTO(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            profile=profile_dto,
            equipment_types=[item.equipment_type.value for item in equipment],
        )


class UpdateUserProfileUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(
        self, user_id: UUID, command: UpdateProfileCommand
    ) -> UserProfileDTO:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        existing = await self.user_repository.get_profile(user_id)
        now = datetime.now(timezone.utc)
        profile = UserProfile(
            id=existing.id if existing else uuid4(),
            user_id=user_id,
            full_name=command.full_name,
            age=command.age,
            height_cm=command.height_cm,
            weight_kg=command.weight_kg,
            training_level=command.training_level,
            primary_goal=command.primary_goal,
            injuries=command.injuries,
            notes=command.notes,
            created_at=existing.created_at if existing and existing.created_at else now,
            updated_at=now,
        )
        saved = await self.user_repository.save_profile(profile)
        return UserProfileDTO(
            user_id=saved.user_id,
            full_name=saved.full_name,
            age=saved.age,
            height_cm=saved.height_cm,
            weight_kg=saved.weight_kg,
            training_level=saved.training_level.value,
            primary_goal=saved.primary_goal.value,
            injuries=saved.injuries,
            notes=saved.notes,
        )


class UpdateUserEquipmentUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(
        self, user_id: UUID, command: UpdateEquipmentCommand
    ) -> UserEquipmentDTO:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        raw_values = [equipment.value for equipment in command.equipment_types]
        if len(set(raw_values)) != len(raw_values):
            raise ValidationError("Equipment list contains duplicates")

        now = datetime.now(timezone.utc)
        equipment = [
            UserEquipment(
                id=uuid4(),
                user_id=user_id,
                equipment_type=equipment_type,
                created_at=now + timedelta(microseconds=index),
            )
            for index, equipment_type in enumerate(command.equipment_types)
        ]
        saved = await self.user_repository.replace_equipment(user_id, equipment)
        return UserEquipmentDTO(
            user_id=user_id,
            equipment_types=[item.equipment_type.value for item in saved],
        )
