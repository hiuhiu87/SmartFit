from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.readiness.commands import CalculateReadinessCommand
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.readiness_schema import (
    CalculateReadinessRequestSchema,
    ReadinessResponseSchema,
)

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.post("/calculate", response_model=APIResponseSchema[ReadinessResponseSchema])
async def calculate_readiness(
    payload: CalculateReadinessRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ReadinessResponseSchema]:
    result = await container.calculate_readiness_use_case(session).execute(
        CalculateReadinessCommand(user_id=user_id, date=payload.date)
    )
    await session.commit()
    return APIResponseSchema(data=ReadinessResponseSchema(**asdict(result)))


@router.get("/today", response_model=APIResponseSchema[ReadinessResponseSchema])
async def get_today_readiness(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ReadinessResponseSchema]:
    result = await container.get_today_readiness_use_case(session).execute(user_id)
    await session.commit()
    return APIResponseSchema(data=ReadinessResponseSchema(**asdict(result)))


@router.get("/history", response_model=APIResponseSchema[list[ReadinessResponseSchema]])
async def get_readiness_history(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[list[ReadinessResponseSchema]]:
    result = await container.get_readiness_history_use_case(session).execute(user_id)
    return APIResponseSchema(
        data=[ReadinessResponseSchema(**asdict(item)) for item in result]
    )
