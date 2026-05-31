from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.common.enums import SubscriptionPlan, SubscriptionStatus
from src.domain.subscription.entities import Subscription
from src.domain.subscription.repositories import SubscriptionRepository
from src.infrastructure.database.models.subscription_model import SubscriptionModel


class SQLModelSubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        statement = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Subscription(
            id=model.id,
            user_id=model.user_id,
            plan=SubscriptionPlan(model.plan),
            status=SubscriptionStatus(model.status),
            started_at=model.started_at,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, subscription: Subscription) -> Subscription:
        model = SubscriptionModel.model_validate(
            {
                "id": subscription.id,
                "user_id": subscription.user_id,
                "plan": subscription.plan.value,
                "status": subscription.status.value,
                "started_at": subscription.started_at,
                "expires_at": subscription.expires_at,
                "created_at": subscription.created_at,
                "updated_at": subscription.updated_at,
            }
        )
        self.session.add(model)
        return subscription
