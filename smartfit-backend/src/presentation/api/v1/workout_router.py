from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends

from app.container import container
from src.application.workout.commands import CompleteWorkoutCommand, GenerateWorkoutCommand, LogSetCommand, StartWorkoutCommand
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.workout_schema import CompleteWorkoutRequestSchema, GenerateWorkoutRequestSchema, LogSetRequestSchema, StartWorkoutRequestSchema

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("/generate", response_model=APIResponseSchema[dict])
async def generate_workout(
    payload: GenerateWorkoutRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
) -> APIResponseSchema[dict]:
    result = await container.generate_workout_use_case().execute(GenerateWorkoutCommand(user_id=user_id, **payload.model_dump()))
    return APIResponseSchema(data=asdict(result))


@router.get("/history", response_model=APIResponseSchema[list[dict]])
async def get_workout_history(_: UUID = Depends(get_current_user_id)) -> APIResponseSchema[list[dict]]:
    result = await container.get_workout_history_use_case().execute()
    return APIResponseSchema(data=[asdict(item) for item in result])


@router.get("/{workout_id}", response_model=APIResponseSchema[dict])
async def get_workout(workout_id: UUID) -> APIResponseSchema[dict]:
    # TODO: call workout detail use case when repository mapping is implemented.
    return APIResponseSchema(data={"workout_id": str(workout_id)})


@router.post("/{workout_id}/start", response_model=APIResponseSchema[dict])
async def start_workout(workout_id: UUID, _: StartWorkoutRequestSchema) -> APIResponseSchema[dict]:
    result = await container.start_workout_use_case().execute(StartWorkoutCommand(workout_id=workout_id))
    return APIResponseSchema(data=asdict(result))


@router.post("/{workout_id}/sets", response_model=APIResponseSchema[dict])
async def log_set(workout_id: UUID, payload: LogSetRequestSchema) -> APIResponseSchema[dict]:
    result = await container.log_workout_set_use_case().execute(LogSetCommand(workout_id=workout_id, **payload.model_dump()))
    return APIResponseSchema(data=result)


@router.post("/{workout_id}/complete", response_model=APIResponseSchema[dict])
async def complete_workout(workout_id: UUID, payload: CompleteWorkoutRequestSchema) -> APIResponseSchema[dict]:
    result = await container.complete_workout_use_case().execute(CompleteWorkoutCommand(workout_id=workout_id, **payload.model_dump()))
    return APIResponseSchema(data=result)

