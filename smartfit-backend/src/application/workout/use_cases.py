from uuid import uuid4

from src.application.workout.commands import CompleteWorkoutCommand, GenerateWorkoutCommand, LogSetCommand, StartWorkoutCommand
from src.application.workout.dto import WorkoutPlanDTO


class GenerateWorkoutUseCase:
    async def execute(self, command: GenerateWorkoutCommand) -> WorkoutPlanDTO:
        # TODO: integrate readiness, AI generation, repository persistence, and safety policy.
        return WorkoutPlanDTO(workout_id=uuid4(), title=f"{command.focus.value.title()} Session", status="generated")


class GetWorkoutDetailUseCase:
    async def execute(self, workout_id):
        raise NotImplementedError("TODO: load workout detail")


class StartWorkoutUseCase:
    async def execute(self, command: StartWorkoutCommand) -> WorkoutPlanDTO:
        # TODO: mark workout as started and create workout log.
        return WorkoutPlanDTO(workout_id=command.workout_id, title="Workout", status="started")


class LogWorkoutSetUseCase:
    async def execute(self, command: LogSetCommand) -> dict[str, str]:
        # TODO: persist workout set log.
        return {"status": "logged", "workout_id": str(command.workout_id)}


class CompleteWorkoutUseCase:
    async def execute(self, command: CompleteWorkoutCommand) -> dict[str, str]:
        # TODO: finalize workout log and feedback pipeline.
        return {"status": "completed", "workout_id": str(command.workout_id)}


class GetWorkoutHistoryUseCase:
    async def execute(self) -> list[WorkoutPlanDTO]:
        return []
