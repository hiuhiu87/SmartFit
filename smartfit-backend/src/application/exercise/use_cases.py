from src.application.exercise.dto import ExerciseDTO, ExerciseListDTO
from src.application.exercise.queries import GetExerciseByIdQuery, ListExercisesQuery
from src.domain.common.exceptions import NotFoundError
from src.domain.exercise.entities import Exercise
from src.domain.exercise.repositories import ExerciseRepository


class ListExercisesUseCase:
    def __init__(self, exercise_repository: ExerciseRepository) -> None:
        self.exercise_repository = exercise_repository

    async def execute(self, query: ListExercisesQuery) -> ExerciseListDTO:
        items, total = await self.exercise_repository.find_by_filters(
            primary_muscle=query.primary_muscle,
            equipment=query.equipment,
            difficulty=query.difficulty,
            movement_type=query.movement_type,
            limit=query.limit,
            offset=query.offset,
        )
        return ExerciseListDTO(
            items=[self._to_dto(item) for item in items],
            limit=query.limit,
            offset=query.offset,
            total=total,
        )

    def _to_dto(self, exercise: Exercise) -> ExerciseDTO:
        return ExerciseDTO(
            id=exercise.id,
            name=exercise.name,
            slug=exercise.slug,
            primary_muscle=exercise.muscle_group.value,
            secondary_muscles=exercise.secondary_muscles,
            equipment=exercise.equipment_type.value,
            difficulty=exercise.training_level.value,
            movement_type=exercise.movement_type,
            instruction=exercise.instruction,
            safety_notes=exercise.safety_notes,
        )


class GetExerciseByIdUseCase:
    def __init__(self, exercise_repository: ExerciseRepository) -> None:
        self.exercise_repository = exercise_repository

    async def execute(self, query: GetExerciseByIdQuery) -> ExerciseDTO:
        exercise = await self.exercise_repository.get_by_id(query.exercise_id)
        if exercise is None:
            raise NotFoundError("Exercise not found.")
        return ExerciseDTO(
            id=exercise.id,
            name=exercise.name,
            slug=exercise.slug,
            primary_muscle=exercise.muscle_group.value,
            secondary_muscles=exercise.secondary_muscles,
            equipment=exercise.equipment_type.value,
            difficulty=exercise.training_level.value,
            movement_type=exercise.movement_type,
            instruction=exercise.instruction,
            safety_notes=exercise.safety_notes,
        )
