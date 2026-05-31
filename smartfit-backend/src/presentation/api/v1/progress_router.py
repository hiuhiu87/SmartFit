from datetime import date as date_type
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.progress.queries import (
    GetPersonalRecordsQuery,
    GetProgressOverviewQuery,
    GetWeeklyReportQuery,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.progress_schema import (
    LatestCompletedWorkoutSchema,
    MuscleDistributionItemSchema,
    PersonalRecordResponseSchema,
    PersonalRecordsResponseSchema,
    ProgressOverviewResponseSchema,
    WeeklyReportResponseSchema,
)

router = APIRouter(prefix="/progress", tags=["progress"])


def _to_overview_schema(result) -> ProgressOverviewResponseSchema:
    return ProgressOverviewResponseSchema(
        from_date=result.from_date,
        to_date=result.to_date,
        weekly_workouts_completed=result.weekly_workouts_completed,
        weekly_workout_target=result.weekly_workout_target,
        consistency_percentage=result.consistency_percentage,
        total_volume_this_week=result.total_volume_this_week,
        average_readiness_this_week=result.average_readiness_this_week,
        completed_workout_days=result.completed_workout_days,
        latest_completed_workout=(
            LatestCompletedWorkoutSchema(
                workout_id=str(result.latest_completed_workout.workout_id),
                workout_log_id=str(result.latest_completed_workout.workout_log_id),
                title=result.latest_completed_workout.title,
                completed_at=result.latest_completed_workout.completed_at,
                duration_minutes=result.latest_completed_workout.duration_minutes,
                total_volume=result.latest_completed_workout.total_volume,
                focus_muscle=result.latest_completed_workout.focus_muscle,
            )
            if result.latest_completed_workout
            else None
        ),
        muscle_distribution=[
            MuscleDistributionItemSchema(
                muscle=item.muscle,
                workout_count=item.workout_count,
                set_count=item.set_count,
                volume=item.volume,
                percentage=item.percentage,
            )
            for item in result.muscle_distribution
        ],
    )


@router.get(
    "/overview", response_model=APIResponseSchema[ProgressOverviewResponseSchema]
)
async def get_overview(
    from_date: date_type | None = Query(default=None),
    to_date: date_type | None = Query(default=None),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ProgressOverviewResponseSchema]:
    result = await container.get_progress_overview_use_case(session).execute(
        GetProgressOverviewQuery(user_id=user_id, from_date=from_date, to_date=to_date)
    )
    return APIResponseSchema(data=_to_overview_schema(result))


@router.get(
    "/personal-records", response_model=APIResponseSchema[PersonalRecordsResponseSchema]
)
async def get_personal_records(
    limit: int = Query(default=20, ge=1, le=100),
    exercise_id: UUID | None = Query(default=None),
    metric: str | None = Query(default=None),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[PersonalRecordsResponseSchema]:
    result = await container.get_personal_records_use_case(session).execute(
        GetPersonalRecordsQuery(
            user_id=user_id, limit=limit, exercise_id=exercise_id, metric=metric
        )
    )
    return APIResponseSchema(
        data=PersonalRecordsResponseSchema(
            items=[
                PersonalRecordResponseSchema(
                    exercise_id=str(item.exercise_id),
                    exercise_name=item.exercise_name,
                    primary_muscle=item.primary_muscle,
                    best_weight=item.best_weight,
                    best_reps=item.best_reps,
                    best_set_volume=item.best_set_volume,
                    estimated_1rm=item.estimated_1rm,
                    workout_id=str(item.workout_id),
                    workout_log_id=str(item.workout_log_id),
                    achieved_at=item.achieved_at,
                )
                for item in result.items
            ],
            limit=result.limit,
            total=result.total,
        )
    )


@router.get(
    "/weekly-report", response_model=APIResponseSchema[WeeklyReportResponseSchema]
)
async def get_weekly_report(
    week_start: date_type | None = Query(default=None),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[WeeklyReportResponseSchema]:
    result = await container.get_weekly_report_use_case(session).execute(
        GetWeeklyReportQuery(user_id=user_id, week_start=week_start)
    )
    return APIResponseSchema(
        data=WeeklyReportResponseSchema(
            week_start=result.week_start,
            week_end=result.week_end,
            summary=result.summary,
            highlights=result.highlights,
            suggestions=result.suggestions,
            overview=_to_overview_schema(result.overview),
        )
    )
