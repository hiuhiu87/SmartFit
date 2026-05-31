from datetime import date as date_type
from datetime import datetime, timezone
from statistics import mean
from uuid import UUID
from uuid import uuid4

from src.application.readiness.commands import CalculateReadinessCommand
from src.application.readiness.dto import ReadinessDTO
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.health.repositories import HealthRepository
from src.domain.readiness.entities import ReadinessScore
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.readiness.services import ReadinessCalculator


class CalculateReadinessUseCase:
    def __init__(
        self,
        readiness_repository: ReadinessRepository,
        health_repository: HealthRepository,
        calculator: ReadinessCalculator | None = None,
    ) -> None:
        self.readiness_repository = readiness_repository
        self.health_repository = health_repository
        self.calculator = calculator or ReadinessCalculator()

    async def execute(self, command: CalculateReadinessCommand) -> ReadinessDTO:
        health_summary = await self.health_repository.get_summary_by_date(
            command.user_id, command.date
        )
        manual_checkin = await self.health_repository.get_manual_checkin_by_date(
            command.user_id, command.date
        )
        if health_summary is None and manual_checkin is None:
            raise ValidationError(
                "Cannot calculate readiness without a health summary or manual check-in"
            )

        recent_summaries = await self.health_repository.get_recent_summaries(
            command.user_id, command.date, limit=7
        )
        hrv_baseline = self._average_metric(
            recent_summaries, "heart_rate_variability", minimum_points=2
        )
        rhr_baseline = self._average_metric(
            recent_summaries, "resting_heart_rate", minimum_points=2
        )

        score, category, recommendation, confidence, explanation = (
            self.calculator.calculate(
                health_summary=health_summary,
                manual_checkin=manual_checkin,
                hrv_baseline=hrv_baseline,
                rhr_baseline=rhr_baseline,
                recent_load_score=70.0,
            )
        )
        now = datetime.now(timezone.utc)
        existing = await self.readiness_repository.get_by_date(command.user_id, command.date)
        saved = await self.readiness_repository.save(
            ReadinessScore(
                id=existing.id if existing else uuid4(),
                user_id=command.user_id,
                date=command.date,
                score=score,
                category=category,
                recommendation=recommendation,
                confidence=confidence,
                explanation=explanation,
                created_at=existing.created_at if existing else now,
                updated_at=now,
            )
        )
        return self._to_dto(saved)

    def _average_metric(
        self,
        summaries: list[HealthSummary],
        field_name: str,
        minimum_points: int,
    ) -> float | None:
        values = [
            value
            for summary in summaries
            if (value := getattr(summary, field_name)) is not None
        ]
        if len(values) < minimum_points:
            return None
        return round(mean(values), 2)

    def _to_dto(self, readiness: ReadinessScore) -> ReadinessDTO:
        return ReadinessDTO(
            date=readiness.date,
            score=readiness.score,
            category=readiness.category.value,
            recommendation=readiness.recommendation.value,
            confidence=readiness.confidence,
            explanation=readiness.explanation,
        )


class GetTodayReadinessUseCase:
    def __init__(
        self,
        readiness_repository: ReadinessRepository,
        calculate_readiness_use_case: CalculateReadinessUseCase,
        health_repository: HealthRepository,
    ) -> None:
        self.readiness_repository = readiness_repository
        self.calculate_readiness_use_case = calculate_readiness_use_case
        self.health_repository = health_repository

    async def execute(self, user_id: UUID) -> ReadinessDTO:
        today = date_type.today()
        existing = await self.readiness_repository.get_by_date(user_id, today)
        if existing is not None:
            return ReadinessDTO(
                date=existing.date,
                score=existing.score,
                category=existing.category.value,
                recommendation=existing.recommendation.value,
                confidence=existing.confidence,
                explanation=existing.explanation,
            )

        health_summary = await self.health_repository.get_summary_by_date(user_id, today)
        manual_checkin = await self.health_repository.get_manual_checkin_by_date(user_id, today)
        if health_summary is None and manual_checkin is None:
            raise NotFoundError("Today's readiness is not available")
        return await self.calculate_readiness_use_case.execute(
            CalculateReadinessCommand(user_id=user_id, date=today)
        )


class GetReadinessHistoryUseCase:
    def __init__(self, readiness_repository: ReadinessRepository) -> None:
        self.readiness_repository = readiness_repository

    async def execute(self, user_id: UUID, limit: int = 30) -> list[ReadinessDTO]:
        history = await self.readiness_repository.list_history(user_id, limit=limit)
        return [
            ReadinessDTO(
                date=item.date,
                score=item.score,
                category=item.category.value,
                recommendation=item.recommendation.value,
                confidence=item.confidence,
                explanation=item.explanation,
            )
            for item in history
        ]
