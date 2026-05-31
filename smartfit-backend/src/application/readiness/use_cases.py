from src.application.readiness.commands import CalculateReadinessCommand
from src.application.readiness.dto import ReadinessDTO
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.readiness.services import ReadinessCalculator


class CalculateReadinessUseCase:
    def __init__(self, calculator: ReadinessCalculator | None = None) -> None:
        self.calculator = calculator or ReadinessCalculator()

    async def execute(
        self,
        command: CalculateReadinessCommand,
        *,
        health_summary: HealthSummary | None = None,
        manual_checkin: ManualCheckin | None = None,
    ) -> ReadinessDTO:
        score, category, recommendation, confidence, explanation = (
            self.calculator.calculate(
                health_summary=health_summary,
                manual_checkin=manual_checkin,
            )
        )
        return ReadinessDTO(
            date=command.date,
            score=score,
            category=category.value,
            recommendation=recommendation.value,
            confidence=confidence,
            explanation=explanation,
        )


class GetTodayReadinessUseCase:
    async def execute(self) -> ReadinessDTO:
        raise NotImplementedError("TODO: load today's readiness from repository")


class GetReadinessHistoryUseCase:
    async def execute(self) -> list[ReadinessDTO]:
        raise NotImplementedError("TODO: load readiness history from repository")
