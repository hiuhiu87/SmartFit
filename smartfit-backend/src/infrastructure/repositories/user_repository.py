from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.user.entities import NotificationSetting, User, UserEquipment, UserPreference, UserProfile
from src.domain.user.repositories import UserRepository
from src.infrastructure.database.mapper import user_model_to_domain, user_profile_model_to_domain
from src.infrastructure.database.models.user_model import UserModel, UserProfileModel


class SQLModelUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return user_model_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return user_model_to_domain(model) if model else None

    async def save(self, user: User) -> User:
        model = UserModel.model_validate(
            {
                "id": user.id,
                "email": user.email,
                "password_hash": user.password_hash,
                "auth_provider": user.auth_provider.value,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        )
        self.session.add(model)
        return user

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        statement = select(UserProfileModel).where(UserProfileModel.user_id == profile.user_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            model = UserProfileModel(user_id=profile.user_id)
            self.session.add(model)

        model.full_name = profile.full_name
        model.age = profile.age
        model.height_cm = profile.height_cm
        model.weight_kg = profile.weight_kg
        model.training_level = profile.training_level.value
        model.primary_goal = profile.primary_goal.value
        model.injuries = profile.injuries
        model.notes = profile.notes
        return user_profile_model_to_domain(model)

    async def replace_equipment(self, user_id: UUID, equipment: list[UserEquipment]) -> list[UserEquipment]:
        # TODO: delete existing equipment rows and insert replacement set.
        return equipment

    async def save_preference(self, preference: UserPreference) -> UserPreference:
        # TODO: persist user preference row.
        return preference

    async def save_notification_setting(self, setting: NotificationSetting) -> NotificationSetting:
        # TODO: persist notification setting row.
        return setting
