from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.program.commands import (
    CreateProgramCommand,
    GenerateTodayProgramWorkoutCommand,
    RescheduleProgramWorkoutCommand,
    SkipProgramWorkoutCommand,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.api.v1.workout_router import _to_workout_plan_response
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.program_schema import (
    CreateProgramRequestSchema,
    ProgramWorkoutPlanResponseSchema,
    RescheduleProgramWorkoutRequestSchema,
    TodayProgramWorkoutResponseSchema,
    TrainingProgramResponseSchema,
)

router = APIRouter(prefix="/programs", tags=["programs"])


@router.post("", response_model=APIResponseSchema[TrainingProgramResponseSchema])
async def create_program(
    payload: CreateProgramRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TrainingProgramResponseSchema]:
    result = await container.program_service(session).create_program(
        CreateProgramCommand(user_id=user_id, **payload.model_dump())
    )
    await session.commit()
    return APIResponseSchema(data=TrainingProgramResponseSchema.model_validate(result))


@router.get("/active", response_model=APIResponseSchema[TrainingProgramResponseSchema])
async def get_active_program(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TrainingProgramResponseSchema]:
    result = await container.program_service(session).get_active_program(user_id)
    return APIResponseSchema(data=TrainingProgramResponseSchema.model_validate(result))


@router.get(
    "/active/today",
    response_model=APIResponseSchema[TodayProgramWorkoutResponseSchema],
)
async def get_today_program_workout(
    target_date: date | None = Query(default=None, alias="date"),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TodayProgramWorkoutResponseSchema]:
    result = await container.program_service(session).get_today(
        user_id, target_date or date.today()
    )
    await session.commit()
    return APIResponseSchema(
        data=TodayProgramWorkoutResponseSchema.model_validate(result)
    )


@router.post(
    "/active/today/generate",
    response_model=APIResponseSchema[ProgramWorkoutPlanResponseSchema],
)
async def generate_today_program_workout(
    target_date: date | None = Query(default=None, alias="date"),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ProgramWorkoutPlanResponseSchema]:
    result = await container.program_service(session).generate_today(
        GenerateTodayProgramWorkoutCommand(
            user_id=user_id, target_date=target_date or date.today()
        )
    )
    await session.commit()
    return APIResponseSchema(data=_to_workout_plan_response(result))


@router.post(
    "/workouts/{instance_id}/skip",
    response_model=APIResponseSchema[TodayProgramWorkoutResponseSchema],
)
async def skip_program_workout(
    instance_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TodayProgramWorkoutResponseSchema]:
    result = await container.program_service(session).skip(
        SkipProgramWorkoutCommand(user_id=user_id, instance_id=instance_id)
    )
    await session.commit()
    return APIResponseSchema(
        data=TodayProgramWorkoutResponseSchema.model_validate(result)
    )


@router.post(
    "/workouts/{instance_id}/reschedule",
    response_model=APIResponseSchema[TodayProgramWorkoutResponseSchema],
)
async def reschedule_program_workout(
    instance_id: UUID,
    payload: RescheduleProgramWorkoutRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TodayProgramWorkoutResponseSchema]:
    result = await container.program_service(session).reschedule(
        RescheduleProgramWorkoutCommand(
            user_id=user_id,
            instance_id=instance_id,
            scheduled_date=payload.scheduled_date,
        )
    )
    await session.commit()
    return APIResponseSchema(
        data=TodayProgramWorkoutResponseSchema.model_validate(result)
    )
