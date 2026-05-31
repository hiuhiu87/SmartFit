from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.application.health.commands import (
    SaveHealthSummaryCommand,
    SaveManualCheckinCommand,
)
from src.application.health.dto import HealthSummaryDTO, ManualCheckinDTO
from src.domain.common.exceptions import NotFoundError
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.health.repositories import HealthRepository


class SaveHealthSummaryUseCase:
    def __init__(self, health_repository: HealthRepository) -> None:
        self.health_repository = health_repository

    async def execute(self, user_id: UUID, command: SaveHealthSummaryCommand) -> HealthSummaryDTO:
        existing = await self.health_repository.get_summary_by_date(user_id, command.date)
        now = datetime.now(timezone.utc)
        saved = await self.health_repository.save_summary(
            HealthSummary(
                id=existing.id if existing else uuid4(),
                user_id=user_id,
                date=command.date,
                sleep_hours=command.sleep_hours,
                sleep_efficiency=command.sleep_efficiency,
                resting_heart_rate=command.resting_heart_rate,
                heart_rate_variability=command.heart_rate_variability,
                steps=command.steps,
                active_energy_kcal=command.active_energy_kcal,
                source="healthkit",
                created_at=existing.created_at if existing else now,
                updated_at=now,
            )
        )
        return HealthSummaryDTO(
            date=saved.date,
            sleep_hours=saved.sleep_hours,
            sleep_efficiency=saved.sleep_efficiency,
            resting_heart_rate=saved.resting_heart_rate,
            heart_rate_variability=saved.heart_rate_variability,
            steps=saved.steps,
            active_energy_kcal=saved.active_energy_kcal,
            source=saved.source,
        )


class SaveManualCheckinUseCase:
    def __init__(self, health_repository: HealthRepository) -> None:
        self.health_repository = health_repository

    async def execute(self, user_id: UUID, command: SaveManualCheckinCommand) -> ManualCheckinDTO:
        existing = await self.health_repository.get_manual_checkin_by_date(user_id, command.date)
        now = datetime.now(timezone.utc)
        saved = await self.health_repository.save_manual_checkin(
            ManualCheckin(
                id=existing.id if existing else uuid4(),
                user_id=user_id,
                date=command.date,
                energy=command.energy,
                soreness=command.soreness,
                stress=command.stress,
                motivation=command.motivation,
                sleep_quality=command.sleep_quality,
                notes=command.notes,
                created_at=existing.created_at if existing else now,
                updated_at=now,
            )
        )
        return ManualCheckinDTO(
            date=saved.date,
            energy=saved.energy,
            soreness=saved.soreness,
            stress=saved.stress,
            motivation=saved.motivation,
            sleep_quality=saved.sleep_quality,
            notes=saved.notes,
        )


class GetLatestHealthSummaryUseCase:
    def __init__(self, health_repository: HealthRepository) -> None:
        self.health_repository = health_repository

    async def execute(self, user_id: UUID) -> HealthSummaryDTO:
        summary = await self.health_repository.get_latest_summary(user_id)
        if summary is None:
            raise NotFoundError("Health summary not found")
        return HealthSummaryDTO(
            date=summary.date,
            sleep_hours=summary.sleep_hours,
            sleep_efficiency=summary.sleep_efficiency,
            resting_heart_rate=summary.resting_heart_rate,
            heart_rate_variability=summary.heart_rate_variability,
            steps=summary.steps,
            active_energy_kcal=summary.active_energy_kcal,
            source=summary.source,
        )
