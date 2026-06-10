from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

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
    ProgramCalendarDayResponseSchema,
)

router = APIRouter(prefix="/programs", tags=["programs"])


class AdjustTodayWorkoutRequest(BaseModel):
    instance_id: UUID
    adjustment_type: str
    reason: str | None = None


class OpenPlannedWorkoutRequest(BaseModel):
    instance_id: UUID


class RegenerateProgramRequest(BaseModel):
    from_week: int


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


@router.get(
    "/active/calendar",
    response_model=APIResponseSchema[list[ProgramCalendarDayResponseSchema]],
)
async def get_active_program_calendar(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[list[ProgramCalendarDayResponseSchema]]:
    result = await container.program_service(session).get_calendar(
        user_id, from_date, to_date
    )
    return APIResponseSchema(
        data=[ProgramCalendarDayResponseSchema.model_validate(item) for item in result]
    )


@router.get(
    "/{program_id}/weeks/{week_number}",
    response_model=APIResponseSchema[dict],
)
async def get_program_week(
    program_id: UUID,
    week_number: int,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.program_service(session).get_week(
        program_id, user_id, week_number
    )
    return APIResponseSchema(data=result)


@router.post(
    "/active/today/open",
    response_model=APIResponseSchema[ProgramWorkoutPlanResponseSchema],
)
async def open_planned_workout(
    payload: OpenPlannedWorkoutRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ProgramWorkoutPlanResponseSchema]:
    result = await container.program_service(session).open_planned_workout(
        user_id=user_id,
        instance_id=payload.instance_id,
    )
    await session.commit()
    return APIResponseSchema(data=_to_workout_plan_response(result))


@router.post(
    "/active/today/adjust",
    response_model=APIResponseSchema[ProgramWorkoutPlanResponseSchema],
)
async def adjust_today_workout(
    payload: AdjustTodayWorkoutRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ProgramWorkoutPlanResponseSchema]:
    result = await container.program_service(session).adjust_today_workout(
        user_id=user_id,
        instance_id=payload.instance_id,
        adjustment_type=payload.adjustment_type,
        reason=payload.reason,
    )
    await session.commit()
    return APIResponseSchema(data=_to_workout_plan_response(result))


@router.post(
    "/{program_id}/regenerate",
    response_model=APIResponseSchema[TrainingProgramResponseSchema],
)
async def regenerate_program(
    program_id: UUID,
    payload: RegenerateProgramRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TrainingProgramResponseSchema]:
    result = await container.program_service(session).regenerate_program(
        program_id=program_id,
        user_id=user_id,
        from_week=payload.from_week,
    )
    await session.commit()
    return APIResponseSchema(data=TrainingProgramResponseSchema.model_validate(result))


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
