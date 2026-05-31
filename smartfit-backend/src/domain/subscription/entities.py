from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.common.enums import SubscriptionPlan, SubscriptionStatus


@dataclass(slots=True)
class Subscription:
    id: UUID
    user_id: UUID
    plan: SubscriptionPlan
    status: SubscriptionStatus
    started_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
