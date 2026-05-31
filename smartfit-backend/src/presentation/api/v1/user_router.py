from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.user.commands import UpdateEquipmentCommand, UpdateProfileCommand
from src.domain.user.entities import User
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import (
    get_current_user,
    get_current_user_id,
)
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.user_schema import (
    EquipmentUpdateRequestSchema,
    ProfileUpdateRequestSchema,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponseSchema[dict])
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    profile = await container.get_current_user_use_case(session).execute(
        current_user.id
    )
    return APIResponseSchema(
        data={
            "user_id": str(profile.user_id),
            "email": profile.email,
            "is_active": profile.is_active,
            "profile": (
                None
                if profile.profile is None
                else {
                    "full_name": profile.profile.full_name,
                    "age": profile.profile.age,
                    "height_cm": profile.profile.height_cm,
                    "weight_kg": profile.profile.weight_kg,
                    "training_level": profile.profile.training_level,
                    "primary_goal": profile.profile.primary_goal,
                    "injuries": profile.profile.injuries,
                    "notes": profile.profile.notes,
                }
            ),
            "equipment_types": profile.equipment_types,
        }
    )


@router.put("/me/profile", response_model=APIResponseSchema[dict])
async def update_profile(
    payload: ProfileUpdateRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.update_profile_use_case(session).execute(
        user_id, UpdateProfileCommand(**payload.model_dump())
    )
    await session.commit()
    return APIResponseSchema(
        data={
            "user_id": str(result.user_id),
            "full_name": result.full_name,
            "age": result.age,
            "height_cm": result.height_cm,
            "weight_kg": result.weight_kg,
            "training_level": result.training_level,
            "primary_goal": result.primary_goal,
            "injuries": result.injuries,
            "notes": result.notes,
        }
    )


@router.put("/me/equipment", response_model=APIResponseSchema[dict])
async def update_equipment(
    payload: EquipmentUpdateRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.update_equipment_use_case(session).execute(
        user_id, UpdateEquipmentCommand(**payload.model_dump())
    )
    await session.commit()
    return APIResponseSchema(
        data={"user_id": str(result.user_id), "equipment_types": result.equipment_types}
    )
