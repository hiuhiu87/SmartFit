from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.health.commands import (
    SaveHealthSummaryCommand,
    SaveManualCheckinCommand,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.health_schema import (
    HealthSummaryRequestSchema,
    ManualCheckinRequestSchema,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.post("/summary", response_model=APIResponseSchema[dict])
async def save_summary(
    payload: HealthSummaryRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.save_health_summary_use_case(session).execute(
        user_id, SaveHealthSummaryCommand(**payload.model_dump())
    )
    await session.commit()
    return APIResponseSchema(data=asdict(result))


@router.post("/manual-checkin", response_model=APIResponseSchema[dict])
async def save_manual_checkin(
    payload: ManualCheckinRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.save_manual_checkin_use_case(session).execute(
        user_id, SaveManualCheckinCommand(**payload.model_dump())
    )
    await session.commit()
    return APIResponseSchema(data=asdict(result))


@router.get("/latest-summary", response_model=APIResponseSchema[dict])
async def get_latest_summary(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.get_latest_health_summary_use_case(session).execute(
        user_id
    )
    return APIResponseSchema(data=asdict(result))
