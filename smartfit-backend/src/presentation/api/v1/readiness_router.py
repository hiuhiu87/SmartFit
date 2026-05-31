from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.container import container
from src.application.readiness.commands import CalculateReadinessCommand
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
) -> APIResponseSchema[ReadinessResponseSchema]:
    result = await container.calculate_readiness_use_case().execute(
        CalculateReadinessCommand(user_id=user_id, date=payload.date)
    )
    return APIResponseSchema(data=ReadinessResponseSchema(**asdict(result)))


@router.get("/today", response_model=APIResponseSchema[ReadinessResponseSchema])
async def get_today_readiness(
    _: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[ReadinessResponseSchema]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="TODO: wire repository-backed today readiness query",
    )


@router.get("/history", response_model=APIResponseSchema[list[ReadinessResponseSchema]])
async def get_readiness_history(
    _: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[list[ReadinessResponseSchema]]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="TODO: wire repository-backed readiness history query",
    )
