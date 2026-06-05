from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.common.enums import EquipmentType, WorkoutStyle
from src.domain.user.entities import (
    NotificationSetting,
    User,
    UserEquipment,
    UserPreference,
    UserProfile,
)
from src.domain.user.repositories import UserRepository
from src.infrastructure.database.mapper import (
    user_domain_to_model,
    user_model_to_domain,
    user_profile_model_to_domain,
)
from src.infrastructure.database.models.user_model import (
    NotificationSettingModel,
    UserEquipmentModel,
    UserModel,
    UserPreferenceModel,
    UserProfileModel,
)


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

    async def create(self, user: User) -> User:
        model = user_domain_to_model(user)
        self.session.add(model)
        await self.session.flush()
        return user_model_to_domain(model)

    async def save(self, user: User) -> User:
        statement = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            return await self.create(user)

        model.email = user.email
        model.password_hash = user.password_hash
        model.auth_provider = user.auth_provider.value
        model.is_active = user.is_active
        model.created_at = user.created_at
        model.updated_at = user.updated_at
        await self.session.flush()
        return user_model_to_domain(model)

    async def get_profile(self, user_id: UUID) -> UserProfile | None:
        statement = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return user_profile_model_to_domain(model) if model else None

    async def list_equipment(self, user_id: UUID) -> list[UserEquipment]:
        statement = (
            select(UserEquipmentModel)
            .where(UserEquipmentModel.user_id == user_id)
            .order_by(UserEquipmentModel.created_at.asc(), UserEquipmentModel.id.asc())
        )
        result = await self.session.execute(statement)
        return [
            UserEquipment(
                id=model.id,
                user_id=model.user_id,
                equipment_type=EquipmentType(model.equipment_type),
                created_at=model.created_at,
            )
            for model in result.scalars().all()
        ]

    async def get_equipment(self, user_id: UUID) -> list[UserEquipment]:
        return await self.list_equipment(user_id)

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        statement = select(UserProfileModel).where(
            UserProfileModel.user_id == profile.user_id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            model = UserProfileModel(id=profile.id, user_id=profile.user_id)
            self.session.add(model)

        model.full_name = profile.full_name
        model.age = profile.age
        model.height_cm = profile.height_cm
        model.weight_kg = profile.weight_kg
        model.training_level = profile.training_level.value
        model.training_style = profile.training_style.value
        model.primary_goal = profile.primary_goal.value
        model.injuries = profile.injuries
        model.notes = profile.notes
        model.created_at = profile.created_at
        model.updated_at = profile.updated_at
        await self.session.flush()
        return user_profile_model_to_domain(model)

    async def replace_equipment(
        self, user_id: UUID, equipment: list[UserEquipment]
    ) -> list[UserEquipment]:
        await self.session.execute(
            delete(UserEquipmentModel).where(UserEquipmentModel.user_id == user_id)
        )
        rows = [
            UserEquipmentModel(
                id=item.id,
                user_id=item.user_id,
                equipment_type=item.equipment_type.value,
                created_at=item.created_at,
            )
            for item in equipment
        ]
        self.session.add_all(rows)
        await self.session.flush()
        return equipment

    async def get_preference(self, user_id: UUID) -> UserPreference | None:
        statement = select(UserPreferenceModel).where(
            UserPreferenceModel.user_id == user_id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return UserPreference(
            id=model.id,
            user_id=model.user_id,
            workout_style=WorkoutStyle(model.workout_style),
            preferred_workout_days=list(model.preferred_workout_days or []),
            preferred_session_minutes=model.preferred_session_minutes,
            dislikes=list(model.dislikes or []),
            metadata=dict(model.preference_metadata or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save_preference(self, preference: UserPreference) -> UserPreference:
        statement = select(UserPreferenceModel).where(
            UserPreferenceModel.user_id == preference.user_id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            model = UserPreferenceModel(id=preference.id, user_id=preference.user_id)
            self.session.add(model)

        model.workout_style = preference.workout_style.value
        model.preferred_workout_days = preference.preferred_workout_days
        model.preferred_session_minutes = preference.preferred_session_minutes
        model.dislikes = preference.dislikes
        model.preference_metadata = preference.metadata
        model.created_at = preference.created_at
        model.updated_at = preference.updated_at
        await self.session.flush()
        return preference

    async def save_notification_setting(
        self, setting: NotificationSetting
    ) -> NotificationSetting:
        statement = select(NotificationSettingModel).where(
            NotificationSettingModel.user_id == setting.user_id
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            model = NotificationSettingModel(id=setting.id, user_id=setting.user_id)
            self.session.add(model)

        model.readiness_push_enabled = setting.readiness_push_enabled
        model.workout_reminder_enabled = setting.workout_reminder_enabled
        model.marketing_enabled = setting.marketing_enabled
        model.quiet_hours_start = setting.quiet_hours_start
        model.quiet_hours_end = setting.quiet_hours_end
        model.created_at = setting.created_at
        model.updated_at = setting.updated_at
        await self.session.flush()
        return setting
