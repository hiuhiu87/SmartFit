from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.user.entities import (
    NotificationSetting,
    User,
    UserEquipment,
    UserPreference,
    UserProfile,
)


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_profile(self, user_id: UUID) -> UserProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def list_equipment(self, user_id: UUID) -> list[UserEquipment]:
        raise NotImplementedError

    @abstractmethod
    async def get_equipment(self, user_id: UUID) -> list[UserEquipment]:
        raise NotImplementedError

    @abstractmethod
    async def save_profile(self, profile: UserProfile) -> UserProfile:
        raise NotImplementedError

    @abstractmethod
    async def replace_equipment(
        self, user_id: UUID, equipment: list[UserEquipment]
    ) -> list[UserEquipment]:
        raise NotImplementedError

    @abstractmethod
    async def get_preference(self, user_id: UUID) -> UserPreference | None:
        raise NotImplementedError

    @abstractmethod
    async def save_preference(self, preference: UserPreference) -> UserPreference:
        raise NotImplementedError

    @abstractmethod
    async def save_notification_setting(
        self, setting: NotificationSetting
    ) -> NotificationSetting:
        raise NotImplementedError
