from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.exercise.queries import GetExerciseByIdQuery, ListExercisesQuery
from src.infrastructure.database.session import get_session
from src.presentation.schemas.common_schema import APIResponseSchema
from src.presentation.schemas.exercise_schema import ExerciseListDataSchema, ExerciseResponseSchema, ReplaceExerciseRequestSchema

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=APIResponseSchema[ExerciseListDataSchema])
async def list_exercises(
    primary_muscle: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ExerciseListDataSchema]:
    result = await container.list_exercises_use_case(session).execute(
        ListExercisesQuery(
            primary_muscle=primary_muscle,
            equipment=equipment,
            difficulty=difficulty,
            movement_type=movement_type,
            limit=limit,
            offset=offset,
        )
    )
    data = ExerciseListDataSchema(
        items=[
            ExerciseResponseSchema(**{**asdict(item), "id": str(item.id)})
            for item in result.items
        ],
        limit=result.limit,
        offset=result.offset,
        total=result.total,
    )
    return APIResponseSchema(data=data)


@router.get("/{exercise_id}", response_model=APIResponseSchema[ExerciseResponseSchema])
async def get_exercise_by_id(
    exercise_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[ExerciseResponseSchema]:
    result = await container.get_exercise_by_id_use_case(session).execute(
        GetExerciseByIdQuery(exercise_id=exercise_id)
    )
    return APIResponseSchema(data=ExerciseResponseSchema(**{**asdict(result), "id": str(result.id)}))


@router.post("/replace", response_model=APIResponseSchema[dict])
async def replace_exercise(
    payload: ReplaceExerciseRequestSchema,
) -> APIResponseSchema[dict]:
    # TODO: call exercise replacement use case when implemented.
    return APIResponseSchema(
        data={"exercise_id": payload.exercise_id, "replacement": None}
    )
