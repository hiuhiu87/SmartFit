from uuid import UUID

from fastapi import APIRouter, Depends

from app.container import container
from src.application.user.commands import UpdateEquipmentCommand, UpdateProfileCommand
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.user_schema import EquipmentUpdateRequestSchema, ProfileUpdateRequestSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponseSchema[dict])
async def get_me(user_id: UUID = Depends(get_current_user_id)) -> APIResponseSchema[dict]:
    profile = await container.get_current_user_use_case().execute(user_id)
    return APIResponseSchema(data={"user_id": str(profile.user_id), "full_name": profile.full_name, "injuries": profile.injuries})


@router.put("/me/profile", response_model=APIResponseSchema[dict])
async def update_profile(
    payload: ProfileUpdateRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[dict]:
    result = await container.update_profile_use_case().execute(user_id, UpdateProfileCommand(**payload.model_dump()))
    return APIResponseSchema(data={"user_id": str(result.user_id), "full_name": result.full_name, "injuries": result.injuries})


@router.put("/me/equipment", response_model=APIResponseSchema[dict])
async def update_equipment(
    payload: EquipmentUpdateRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[dict]:
    result = await container.update_equipment_use_case().execute(user_id, UpdateEquipmentCommand(**payload.model_dump()))
    return APIResponseSchema(data={"user_id": str(result.user_id), "equipment_types": result.equipment_types})
