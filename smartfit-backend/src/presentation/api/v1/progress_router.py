from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends

from app.container import container
from src.application.progress.queries import PersonalRecordsQuery, ProgressOverviewQuery
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.progress_schema import (
    PersonalRecordsResponseSchema,
    ProgressOverviewResponseSchema,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get(
    "/overview", response_model=APIResponseSchema[ProgressOverviewResponseSchema]
)
async def get_overview(
    user_id: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[ProgressOverviewResponseSchema]:
    result = await container.get_progress_overview_use_case().execute(
        ProgressOverviewQuery(user_id=user_id)
    )
    return APIResponseSchema(data=ProgressOverviewResponseSchema(**asdict(result)))


@router.get(
    "/personal-records", response_model=APIResponseSchema[PersonalRecordsResponseSchema]
)
async def get_personal_records(
    user_id: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[PersonalRecordsResponseSchema]:
    result = await container.get_personal_records_use_case().execute(
        PersonalRecordsQuery(user_id=user_id)
    )
    return APIResponseSchema(data=PersonalRecordsResponseSchema(records=result.records))
