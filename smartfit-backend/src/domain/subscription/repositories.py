from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.subscription.entities import Subscription


class SubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, subscription: Subscription) -> Subscription:
        raise NotImplementedError
