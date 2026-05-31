from fastapi import APIRouter

from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.exercise_schema import ReplaceExerciseRequestSchema

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=APIResponseSchema[list[dict]])
async def list_exercises() -> APIResponseSchema[list[dict]]:
    # TODO: call exercise listing use case when query use cases are added.
    return APIResponseSchema(data=[])


@router.post("/replace", response_model=APIResponseSchema[dict])
async def replace_exercise(payload: ReplaceExerciseRequestSchema) -> APIResponseSchema[dict]:
    # TODO: call exercise replacement use case when implemented.
    return APIResponseSchema(data={"exercise_id": payload.exercise_id, "replacement": None})
