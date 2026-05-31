from src.application.health.commands import SaveHealthSummaryCommand, SaveManualCheckinCommand
from src.application.health.dto import HealthSummaryDTO, ManualCheckinDTO


class SaveHealthSummaryUseCase:
    async def execute(self, command: SaveHealthSummaryCommand) -> HealthSummaryDTO:
        # TODO: persist HealthKit summary in repository.
        return HealthSummaryDTO(
            date=command.date,
            sleep_hours=command.sleep_hours,
            resting_heart_rate=command.resting_heart_rate,
            heart_rate_variability=command.heart_rate_variability,
        )


class SaveManualCheckinUseCase:
    async def execute(self, command: SaveManualCheckinCommand) -> ManualCheckinDTO:
        # TODO: persist manual check-in in repository.
        return ManualCheckinDTO(
            date=command.date,
            energy=command.energy,
            soreness=command.soreness,
            stress=command.stress,
            motivation=command.motivation,
            sleep_quality=command.sleep_quality,
        )
