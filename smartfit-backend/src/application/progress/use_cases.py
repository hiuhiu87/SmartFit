from datetime import date as date_type
from datetime import datetime, timezone
from datetime import timedelta

from src.application.progress.dto import (
    LatestCompletedWorkoutDTO,
    MuscleDistributionItemDTO,
    PersonalRecordDTO,
    PersonalRecordsDTO,
    ProgressOverviewDTO,
    WeeklyReportDTO,
)
from src.application.progress.queries import (
    GetPersonalRecordsQuery,
    GetProgressOverviewQuery,
    GetWeeklyReportQuery,
)
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.progress.entities import MuscleDistributionItem, ProgressOverview
from src.domain.progress.repositories import ProgressRepository
from src.domain.progress.services import ProgressCalculator
from src.domain.user.repositories import UserRepository


class GetProgressOverviewUseCase:
    def __init__(
        self,
        progress_repository: ProgressRepository,
        user_repository: UserRepository,
        calculator: ProgressCalculator,
    ) -> None:
        self.progress_repository = progress_repository
        self.user_repository = user_repository
        self.calculator = calculator

    async def execute(self, query: GetProgressOverviewQuery) -> ProgressOverviewDTO:
        from_date, to_date = self._resolve_range(query.from_date, query.to_date)

        profile = await self.user_repository.get_profile(query.user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")
        preference = await self.user_repository.get_preference(query.user_id)
        weekly_target = len(preference.preferred_workout_days) if preference else 0

        completed_logs = await self.progress_repository.get_completed_workout_logs(
            query.user_id, from_date, to_date
        )
        total_volume = await self.progress_repository.get_total_volume(
            query.user_id, from_date, to_date
        )
        average_readiness = await self.progress_repository.get_average_readiness(
            query.user_id, from_date, to_date
        )
        muscle_distribution = await self.progress_repository.get_muscle_distribution(
            query.user_id, from_date, to_date
        )
        muscle_distribution = self.calculator.calculate_muscle_percentages(
            muscle_distribution
        )

        completed_days = sorted(
            {log.completed_at.date() for log in completed_logs if log.completed_at is not None}
        )
        latest = completed_logs[0] if completed_logs else None

        overview = ProgressOverview(
            from_date=from_date,
            to_date=to_date,
            weekly_workouts_completed=len(completed_logs),
            weekly_workout_target=weekly_target,
            consistency_percentage=self.calculator.calculate_consistency(
                len(completed_logs), weekly_target
            ),
            total_volume=total_volume,
            average_readiness=average_readiness,
            completed_workout_days=completed_days,
            latest_completed_workout=(
                LatestCompletedWorkoutDTO(
                    workout_id=latest.workout_plan_id,
                    workout_log_id=latest.id,
                    title=latest.title or "Completed Workout",
                    completed_at=latest.completed_at,
                    duration_minutes=latest.duration_minutes,
                    total_volume=latest.total_volume,
                    focus_muscle=latest.focus_muscle or "full_body",
                )
                if latest and latest.completed_at
                else None
            ),
            muscle_distribution=muscle_distribution,
        )
        return self._to_dto(overview)

    def _resolve_range(
        self, from_date: date_type | None, to_date: date_type | None
    ) -> tuple[date_type, date_type]:
        if from_date and to_date and from_date > to_date:
            raise ValidationError("from_date must be less than or equal to to_date.")
        if from_date and to_date:
            return from_date, to_date

        today = datetime.now(timezone.utc).date()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return from_date or monday, to_date or sunday

    def _to_dto(self, overview: ProgressOverview) -> ProgressOverviewDTO:
        latest = overview.latest_completed_workout
        return ProgressOverviewDTO(
            from_date=overview.from_date,
            to_date=overview.to_date,
            weekly_workouts_completed=overview.weekly_workouts_completed,
            weekly_workout_target=overview.weekly_workout_target,
            consistency_percentage=overview.consistency_percentage,
            total_volume_this_week=overview.total_volume,
            average_readiness_this_week=overview.average_readiness,
            completed_workout_days=overview.completed_workout_days,
            latest_completed_workout=latest,
            muscle_distribution=[
                MuscleDistributionItemDTO(
                    muscle=item.muscle,
                    workout_count=item.workout_count,
                    set_count=item.set_count,
                    volume=item.volume,
                    percentage=item.percentage,
                )
                for item in overview.muscle_distribution
            ],
        )


class GetPersonalRecordsUseCase:
    ALLOWED_METRICS = {None, "estimated_1rm", "max_weight", "max_reps", "max_volume"}

    def __init__(
        self, progress_repository: ProgressRepository, calculator: ProgressCalculator
    ) -> None:
        self.progress_repository = progress_repository
        self.calculator = calculator

    async def execute(self, query: GetPersonalRecordsQuery) -> PersonalRecordsDTO:
        if query.metric not in self.ALLOWED_METRICS:
            raise ValidationError("Invalid metric.")

        records = await self.progress_repository.get_personal_records(
            query.user_id, query.limit, query.exercise_id, query.metric
        )
        return PersonalRecordsDTO(
            items=[
                PersonalRecordDTO(
                    exercise_id=item.exercise_id,
                    exercise_name=item.exercise_name,
                    primary_muscle=item.primary_muscle,
                    best_weight=item.best_weight,
                    best_reps=item.best_reps,
                    best_set_volume=item.best_set_volume,
                    estimated_1rm=item.estimated_1rm,
                    workout_id=item.workout_id,
                    workout_log_id=item.workout_log_id,
                    achieved_at=item.achieved_at,
                )
                for item in records
            ],
            limit=query.limit,
            total=len(records),
        )


class GetWeeklyReportUseCase:
    def __init__(
        self,
        overview_use_case: GetProgressOverviewUseCase,
        calculator: ProgressCalculator,
    ) -> None:
        self.overview_use_case = overview_use_case
        self.calculator = calculator

    async def execute(self, query: GetWeeklyReportQuery) -> WeeklyReportDTO:
        today = datetime.now(timezone.utc).date()
        week_start = query.week_start or (today - timedelta(days=today.weekday()))
        week_end = week_start + timedelta(days=6)
        overview = await self.overview_use_case.execute(
            GetProgressOverviewQuery(
                user_id=query.user_id,
                from_date=week_start,
                to_date=week_end,
            )
        )
        highlights, suggestions = self.calculator.build_weekly_insights(
            ProgressOverview(
                from_date=overview.from_date,
                to_date=overview.to_date,
                weekly_workouts_completed=overview.weekly_workouts_completed,
                weekly_workout_target=overview.weekly_workout_target,
                consistency_percentage=overview.consistency_percentage,
                total_volume=overview.total_volume_this_week,
                average_readiness=overview.average_readiness_this_week,
                completed_workout_days=overview.completed_workout_days,
                latest_completed_workout=overview.latest_completed_workout,
                muscle_distribution=[
                    MuscleDistributionItem(
                        muscle=item.muscle,
                        workout_count=item.workout_count,
                        set_count=item.set_count,
                        volume=item.volume,
                        percentage=item.percentage,
                    )
                    for item in overview.muscle_distribution
                ],
            )
        )
        summary = (
            f"You completed {overview.weekly_workouts_completed} out of "
            f"{overview.weekly_workout_target} planned workouts this week."
        )
        return WeeklyReportDTO(
            week_start=week_start,
            week_end=week_end,
            summary=summary,
            highlights=highlights,
            suggestions=suggestions,
            overview=overview,
        )
