from src.application.workout.commands import GenerateWorkoutCommand
from src.application.workout.dto import WorkoutPlanDTO
from src.application.workout.use_cases import GenerateWorkoutUseCase
from src.domain.program.entities import ProgramWorkoutInstance, ProgramWorkoutTemplate
from src.domain.program.repositories import ProgramRepository


class ProgramWorkoutGenerator:
    def __init__(
        self,
        workout_generator: GenerateWorkoutUseCase,
        program_repository: ProgramRepository,
    ) -> None:
        self.workout_generator = workout_generator
        self.program_repository = program_repository

    async def generate(
        self,
        *,
        instance: ProgramWorkoutInstance,
        template: ProgramWorkoutTemplate,
        goal: str,
        generation_mode: str,
        training_style: str,
    ) -> WorkoutPlanDTO:
        result = await self.workout_generator.execute(
            GenerateWorkoutCommand(
                user_id=instance.user_id,
                target_date=instance.scheduled_date,
                focus_muscle=template.focus_type,
                available_time_minutes=template.estimated_duration_minutes,
                workout_split=template.workout_type,
                generation_mode=generation_mode,
                goal_override=goal,
                training_style_override=training_style,
            )
        )
        await self.program_repository.link_workout_plan_to_instance(
            instance.id, result.workout_id, result.training_decision
        )
        return result
