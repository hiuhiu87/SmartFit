from datetime import date as date_type
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.workout.commands import (
    CompleteWorkoutCommand,
    GenerateWorkoutCommand,
    LogWorkoutSetCommand,
    StartWorkoutCommand,
)
from src.application.workout.queries import (
    GetWorkoutDetailQuery,
    GetWorkoutHistoryQuery,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.workout_schema import (
    CompleteWorkoutRequestSchema,
    CompleteWorkoutResponseSchema,
    GenerateWorkoutRequestSchema,
    LogSetRequestSchema,
    LogSetResponseSchema,
    LoggedSetResponseSchema,
    StartWorkoutRequestSchema,
    StartWorkoutResponseSchema,
    WorkoutDetailResponseSchema,
    WorkoutExerciseResponseSchema,
    WorkoutHistoryItemSchema,
    WorkoutHistoryResponseSchema,
    WorkoutPlanResponseSchema,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _to_workout_plan_response(result) -> WorkoutPlanResponseSchema:
    return WorkoutPlanResponseSchema(
        workout_id=str(result.workout_id),
        workout_log_id=str(result.workout_log_id) if result.workout_log_id else None,
        title=result.title,
        goal=result.goal,
        focus_muscle=result.focus_muscle,
        estimated_duration_minutes=result.estimated_duration_minutes,
        training_decision=result.training_decision,
        ai_reasoning_summary=result.ai_reasoning_summary,
        safety_note=result.safety_note,
        status=result.status,
        source=result.source,
        exercises=[
            WorkoutExerciseResponseSchema(
                workout_plan_exercise_id=str(item.workout_plan_exercise_id),
                exercise_id=str(item.exercise_id),
                name=item.name,
                order_index=item.order_index,
                primary_muscle=item.primary_muscle,
                equipment=item.equipment,
                target_sets=item.target_sets,
                target_reps=item.target_reps,
                target_weight=item.target_weight,
                rest_seconds=item.rest_seconds,
                target_rpe=item.target_rpe,
                notes=item.notes,
                logged_sets=[
                    LoggedSetResponseSchema(
                        set_log_id=str(set_item.set_log_id),
                        set_number=set_item.set_number,
                        weight=set_item.weight,
                        reps=set_item.reps,
                        rpe=set_item.rpe,
                        completed=set_item.completed,
                    )
                    for set_item in item.logged_sets
                ],
            )
            for item in result.exercises
        ],
    )


@router.post("/generate", response_model=APIResponseSchema[WorkoutPlanResponseSchema])
async def generate_workout(
    payload: GenerateWorkoutRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[WorkoutPlanResponseSchema]:
    result = await container.generate_workout_use_case(session).execute(
        GenerateWorkoutCommand(
            user_id=user_id,
            target_date=payload.date,
            **payload.model_dump(exclude={"date"}),
        )
    )
    await session.commit()
    return APIResponseSchema(data=_to_workout_plan_response(result))


@router.get("/history", response_model=APIResponseSchema[WorkoutHistoryResponseSchema])
async def get_workout_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    from_date: date_type | None = Query(default=None),
    to_date: date_type | None = Query(default=None),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[WorkoutHistoryResponseSchema]:
    result = await container.get_workout_history_use_case(session).execute(
        GetWorkoutHistoryQuery(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status,
            from_date=from_date,
            to_date=to_date,
        )
    )
    return APIResponseSchema(
        data=WorkoutHistoryResponseSchema(
            items=[
                WorkoutHistoryItemSchema(
                    workout_id=str(item.workout_id),
                    workout_log_id=(
                        str(item.workout_log_id) if item.workout_log_id else None
                    ),
                    title=item.title,
                    date=item.date,
                    status=item.status,
                    duration_minutes=item.duration_minutes,
                    total_volume=item.total_volume,
                    difficulty_feedback=item.difficulty_feedback,
                    focus_muscle=item.focus_muscle,
                    training_decision=item.training_decision,
                    source=item.source,
                )
                for item in result.items
            ],
            limit=result.limit,
            offset=result.offset,
            total=result.total,
        )
    )


@router.get(
    "/{workout_id}", response_model=APIResponseSchema[WorkoutDetailResponseSchema]
)
async def get_workout(
    workout_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[WorkoutDetailResponseSchema]:
    result = await container.get_workout_detail_use_case(session).execute(
        GetWorkoutDetailQuery(user_id=user_id, workout_id=workout_id)
    )
    return APIResponseSchema(
        data=WorkoutDetailResponseSchema(
            **_to_workout_plan_response(result).model_dump()
        )
    )


@router.post(
    "/{workout_id}/start",
    response_model=APIResponseSchema[StartWorkoutResponseSchema],
)
async def start_workout(
    workout_id: UUID,
    payload: StartWorkoutRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[StartWorkoutResponseSchema]:
    result = await container.start_workout_use_case(session).execute(
        StartWorkoutCommand(
            user_id=user_id,
            workout_id=workout_id,
            started_at=payload.started_at or datetime.now(timezone.utc),
        )
    )
    await session.commit()
    return APIResponseSchema(
        data=StartWorkoutResponseSchema(
            workout_id=str(result.workout_id),
            workout_log_id=str(result.workout_log_id),
            status=result.status,
            started_at=result.started_at,
        )
    )


@router.post(
    "/{workout_id}/sets", response_model=APIResponseSchema[LogSetResponseSchema]
)
async def log_set(
    workout_id: UUID,
    payload: LogSetRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[LogSetResponseSchema]:
    result = await container.log_workout_set_use_case(session).execute(
        LogWorkoutSetCommand(
            user_id=user_id,
            workout_id=workout_id,
            workout_log_id=payload.workout_log_id,
            workout_plan_exercise_id=payload.workout_plan_exercise_id,
            set_number=payload.set_number,
            weight=payload.weight,
            reps=payload.reps,
            rpe=payload.rpe,
            completed=payload.completed,
        )
    )
    await session.commit()
    return APIResponseSchema(
        data=LogSetResponseSchema(
            set_log_id=str(result.set_log_id),
            workout_log_id=str(result.workout_log_id),
            workout_plan_exercise_id=str(result.workout_plan_exercise_id),
            set_number=result.set_number,
        )
    )


@router.post(
    "/{workout_id}/complete",
    response_model=APIResponseSchema[CompleteWorkoutResponseSchema],
)
async def complete_workout(
    workout_id: UUID,
    payload: CompleteWorkoutRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[CompleteWorkoutResponseSchema]:
    result = await container.complete_workout_use_case(session).execute(
        CompleteWorkoutCommand(
            user_id=user_id,
            workout_id=workout_id,
            workout_log_id=payload.workout_log_id,
            completed_at=payload.completed_at or datetime.now(timezone.utc),
            duration_minutes=payload.duration_minutes,
            calories_burned=payload.calories_burned,
            avg_heart_rate=payload.avg_heart_rate,
            difficulty_feedback=payload.difficulty_feedback,
            energy_after=payload.energy_after,
            notes=payload.notes,
        )
    )
    await session.commit()
    return APIResponseSchema(
        data=CompleteWorkoutResponseSchema(
            workout_id=str(result.workout_id),
            workout_log_id=str(result.workout_log_id),
            status=result.status,
            total_volume=result.total_volume,
            completed_at=result.completed_at,
        )
    )
