from datetime import datetime, timezone
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.health.repositories import HealthRepository
from src.infrastructure.database.mapper import (
    health_summary_model_to_domain,
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
        statement = select(HealthSummaryModel).where(
            HealthSummaryModel.user_id == summary.user_id,
            HealthSummaryModel.date == summary.date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            model = HealthSummaryModel(
                id=summary.id or uuid4(),
                user_id=summary.user_id,
                date=summary.date,
            )
            self.session.add(model)

        model.sleep_hours = summary.sleep_hours
        model.sleep_efficiency = summary.sleep_efficiency
        model.resting_heart_rate = summary.resting_heart_rate
        model.heart_rate_variability = summary.heart_rate_variability
        model.steps = summary.steps
        model.active_energy_kcal = summary.active_energy_kcal
        model.source = summary.source
        model.created_at = summary.created_at or model.created_at or datetime.now(timezone.utc)
        model.updated_at = summary.updated_at or datetime.now(timezone.utc)
        await self.session.flush()
        return health_summary_model_to_domain(model)

    async def save_manual_checkin(self, checkin: ManualCheckin) -> ManualCheckin:
        statement = select(ManualCheckinModel).where(
            ManualCheckinModel.user_id == checkin.user_id,
            ManualCheckinModel.date == checkin.date,
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()

        if model is None:
            model = ManualCheckinModel(
                id=checkin.id or uuid4(),
                user_id=checkin.user_id,
                date=checkin.date,
            )
            self.session.add(model)

        model.energy = checkin.energy
        model.soreness = checkin.soreness
        model.stress = checkin.stress
        model.motivation = checkin.motivation
        model.sleep_quality = checkin.sleep_quality
        model.notes = checkin.notes
        model.created_at = checkin.created_at or model.created_at or datetime.now(timezone.utc)
        model.updated_at = checkin.updated_at or datetime.now(timezone.utc)
        await self.session.flush()
        return manual_checkin_model_to_domain(model)

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

    async def get_latest_summary(self, user_id: UUID) -> HealthSummary | None:
        statement = (
            select(HealthSummaryModel)
            .where(HealthSummaryModel.user_id == user_id)
            .order_by(HealthSummaryModel.date.desc(), HealthSummaryModel.updated_at.desc())
        )
        result = await self.session.execute(statement)
        model = result.scalars().first()
        return health_summary_model_to_domain(model) if model else None

    async def get_recent_summaries(
        self, user_id: UUID, before_date: date, limit: int
    ) -> list[HealthSummary]:
        statement = (
            select(HealthSummaryModel)
            .where(
                HealthSummaryModel.user_id == user_id,
                HealthSummaryModel.date < before_date,
            )
            .order_by(HealthSummaryModel.date.desc(), HealthSummaryModel.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [
            health_summary_model_to_domain(model) for model in result.scalars().all()
        ]

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
