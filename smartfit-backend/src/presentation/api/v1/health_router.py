from dataclasses import asdict

from fastapi import APIRouter

from app.container import container
from src.application.health.commands import (
    SaveHealthSummaryCommand,
    SaveManualCheckinCommand,
)
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.health_schema import (
    HealthSummaryRequestSchema,
    ManualCheckinRequestSchema,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.post("/summary", response_model=APIResponseSchema[dict])
async def save_summary(payload: HealthSummaryRequestSchema) -> APIResponseSchema[dict]:
    result = await container.save_health_summary_use_case().execute(
        SaveHealthSummaryCommand(**payload.model_dump())
    )
    return APIResponseSchema(data=asdict(result))


@router.post("/manual-checkin", response_model=APIResponseSchema[dict])
async def save_manual_checkin(
    payload: ManualCheckinRequestSchema,
) -> APIResponseSchema[dict]:
    result = await container.save_manual_checkin_use_case().execute(
        SaveManualCheckinCommand(**payload.model_dump())
    )
    return APIResponseSchema(data=asdict(result))
