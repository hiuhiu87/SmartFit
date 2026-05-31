from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.health.repositories import HealthRepository
from src.infrastructure.database.mapper import (
    health_summary_domain_to_model,
    health_summary_model_to_domain,
    manual_checkin_domain_to_model,
    manual_checkin_model_to_domain,
)
from src.infrastructure.database.models.health_model import (
    HealthSummaryModel,
    ManualCheckinModel,
)


class SQLModelHealthRepository(HealthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_summary(self, summary: HealthSummary) -> HealthSummary:
        model = health_summary_domain_to_model(summary)
        self.session.add(model)
        return summary

    async def save_manual_checkin(self, checkin: ManualCheckin) -> ManualCheckin:
        model = manual_checkin_domain_to_model(checkin)
        self.session.add(model)
        return checkin

    async def get_summary_by_date(
        self, user_id: UUID, target_date: date
    ) -> HealthSummary | None:
        statement = select(HealthSummaryModel).where(
            HealthSummaryModel.user_id == user_id,
            HealthSummaryModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return health_summary_model_to_domain(model) if model else None

    async def get_manual_checkin_by_date(
        self, user_id: UUID, target_date: date
    ) -> ManualCheckin | None:
        statement = select(ManualCheckinModel).where(
            ManualCheckinModel.user_id == user_id,
            ManualCheckinModel.date == target_date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return manual_checkin_model_to_domain(model) if model else None
