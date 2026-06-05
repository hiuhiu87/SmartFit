from datetime import date, timedelta
from uuid import UUID, uuid4

from src.application.program.commands import (
    CreateProgramCommand,
    GenerateTodayProgramWorkoutCommand,
    RescheduleProgramWorkoutCommand,
    SkipProgramWorkoutCommand,
)
from src.application.program.dto import (
    ProgramSlotDTO,
    ProgramTemplateDTO,
    TodayProgramWorkoutDTO,
    TrainingProgramDTO,
)
from src.application.program.generator import ProgramWorkoutGenerator
from src.application.workout.dto import WorkoutPlanDTO
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.program.entities import (
    PreferredSplit,
    ProgramStatus,
    ProgramWorkoutStatus,
    TrainingProgram,
)
from src.domain.program.repositories import ProgramRepository
from src.domain.program.services import ProgramScheduler, ProgramTemplateFactory
from src.domain.user.repositories import UserRepository


class ProgramService:
    def __init__(
        self,
        repository: ProgramRepository,
        user_repository: UserRepository,
        template_factory: ProgramTemplateFactory,
        scheduler: ProgramScheduler,
        workout_generator: ProgramWorkoutGenerator,
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository
        self.template_factory = template_factory
        self.scheduler = scheduler
        self.workout_generator = workout_generator

    async def create_program(self, command: CreateProgramCommand) -> TrainingProgramDTO:
        profile = await self.user_repository.get_profile(command.user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")
        if not 2 <= command.days_per_week <= 5:
            raise ValidationError("days_per_week must be between 2 and 5.")
        if not 1 <= command.duration_weeks <= 52:
            raise ValidationError("duration_weeks must be between 1 and 52.")

        start_date = command.start_date or date.today()
        program_id = uuid4()
        preferred_split = PreferredSplit(command.preferred_split)
        program = TrainingProgram(
            id=program_id,
            user_id=command.user_id,
            name=f"{command.duration_weeks}-Week {command.goal.replace('_', ' ').title()} Program",
            goal=command.goal,
            training_level=profile.training_level.value,
            training_style=command.training_style or profile.training_style.value,
            duration_weeks=command.duration_weeks,
            days_per_week=command.days_per_week,
            session_duration_minutes=command.session_duration_minutes,
            preferred_split=preferred_split,
            status=ProgramStatus.ACTIVE,
            start_date=start_date,
            end_date=start_date
            + timedelta(weeks=command.duration_weeks)
            - timedelta(days=1),
            generation_mode=command.generation_mode,
            focus_areas=command.focus_areas,
        )
        program.templates = self.template_factory.create_weekly_structure(
            program_id=program.id,
            goal=program.goal,
            days_per_week=program.days_per_week,
            level=program.training_level,
            preferred_split=program.preferred_split,
            focus_areas=program.focus_areas,
            session_duration_minutes=program.session_duration_minutes,
            training_style=program.training_style,
        )
        return self._program_dto(await self.repository.create_program(program))

    async def get_active_program(self, user_id: UUID) -> TrainingProgramDTO:
        program = await self.repository.get_active_program(user_id)
        if program is None:
            raise NotFoundError("Active training program not found.")
        return self._program_dto(program)

    async def get_today(
        self, user_id: UUID, target_date: date
    ) -> TodayProgramWorkoutDTO:
        program = await self.repository.get_active_program(user_id)
        if program is None:
            raise NotFoundError("Active training program not found.")
        existing = await self.repository.get_today_instance(program.id, target_date)
        if existing is not None:
            template = next(
                item
                for item in program.templates
                if item.id == existing.program_workout_template_id
            )
            return self._today_instance_dto(existing, template)

        week_number, day_index = self.scheduler.calculate_position(program, target_date)
        if day_index is None:
            return TodayProgramWorkoutDTO(
                program_id=program.id,
                scheduled=False,
                recommendation="rest_day",
                week_number=week_number or None,
            )

        template = next(
            item for item in program.templates if item.day_index == day_index
        )
        instance = await self.repository.create_or_get_today_instance(
            self.scheduler.build_instance(program, template, target_date)
        )
        if instance.scheduled_date != target_date:
            return TodayProgramWorkoutDTO(
                program_id=program.id,
                scheduled=False,
                recommendation="rest_day",
                week_number=week_number,
            )
        await self.repository.update_program_progress(
            program.id, week_number, day_index
        )
        return self._today_instance_dto(instance, template)

    async def generate_today(
        self, command: GenerateTodayProgramWorkoutCommand
    ) -> WorkoutPlanDTO:
        today = await self.get_today(command.user_id, command.target_date)
        if not today.scheduled or today.instance_id is None or today.template is None:
            raise ValidationError("No program workout is scheduled for today.")
        instance = await self.repository.get_instance_by_id(
            today.instance_id, command.user_id
        )
        if instance is None:
            raise NotFoundError("Program workout instance not found.")
        if instance.actual_workout_plan_id is not None:
            raise ValidationError("Today's program workout has already been generated.")
        if instance.status not in {
            ProgramWorkoutStatus.SCHEDULED,
            ProgramWorkoutStatus.RESCHEDULED,
        }:
            raise ValidationError(
                f"Program workout cannot be generated from status "
                f"'{instance.status.value}'."
            )

        program = await self.repository.get_program_by_id(
            today.program_id, command.user_id
        )
        if program is None:
            raise NotFoundError("Training program not found.")
        template = next(
            item
            for item in program.templates
            if item.id == instance.program_workout_template_id
        )
        return await self.workout_generator.generate(
            instance=instance,
            template=template,
            goal=program.goal,
            generation_mode=program.generation_mode,
            training_style=program.training_style,
        )

    async def skip(self, command: SkipProgramWorkoutCommand) -> TodayProgramWorkoutDTO:
        instance = await self.repository.get_instance_by_id(
            command.instance_id, command.user_id
        )
        if instance is None:
            raise NotFoundError("Program workout instance not found.")
        if instance.status in {
            ProgramWorkoutStatus.STARTED,
            ProgramWorkoutStatus.COMPLETED,
        }:
            raise ValidationError("A started or completed workout cannot be skipped.")
        instance = await self.repository.update_instance_status(
            instance.id, ProgramWorkoutStatus.SKIPPED
        )
        return self._instance_dto(instance, "workout_skipped")

    async def reschedule(
        self, command: RescheduleProgramWorkoutCommand
    ) -> TodayProgramWorkoutDTO:
        instance = await self.repository.get_instance_by_id(
            command.instance_id, command.user_id
        )
        if instance is None:
            raise NotFoundError("Program workout instance not found.")
        if instance.status in {
            ProgramWorkoutStatus.STARTED,
            ProgramWorkoutStatus.COMPLETED,
        }:
            raise ValidationError(
                "A started or completed workout cannot be rescheduled."
            )
        program = await self.repository.get_program_by_id(
            instance.program_id, command.user_id
        )
        if program is None or not (
            program.start_date <= command.scheduled_date <= program.end_date
        ):
            raise ValidationError("Rescheduled date must be within the program.")
        instance = await self.repository.update_instance_status(
            instance.id,
            ProgramWorkoutStatus.RESCHEDULED,
            command.scheduled_date,
        )
        return self._instance_dto(instance, "workout_rescheduled")

    def _program_dto(self, program: TrainingProgram) -> TrainingProgramDTO:
        return TrainingProgramDTO(
            id=program.id,
            name=program.name,
            goal=program.goal,
            training_level=program.training_level,
            training_style=program.training_style,
            duration_weeks=program.duration_weeks,
            days_per_week=program.days_per_week,
            session_duration_minutes=program.session_duration_minutes,
            preferred_split=program.preferred_split.value,
            status=program.status.value,
            start_date=program.start_date,
            end_date=program.end_date,
            current_week=program.current_week,
            current_day_index=program.current_day_index,
            generation_mode=program.generation_mode,
            focus_areas=program.focus_areas,
            weekly_structure=[self._template_dto(item) for item in program.templates],
        )

    def _template_dto(self, template) -> ProgramTemplateDTO:
        return ProgramTemplateDTO(
            id=template.id,
            day_index=template.day_index,
            title=template.title,
            focus_type=template.focus_type,
            workout_type=template.workout_type,
            estimated_duration_minutes=template.estimated_duration_minutes,
            sequence_order=template.sequence_order,
            slots=[
                ProgramSlotDTO(
                    id=slot.id,
                    slot_order=slot.slot_order,
                    slot_type=slot.slot_type,
                    movement_patterns=slot.movement_patterns,
                    primary_muscles=slot.primary_muscles,
                    exercise_roles=slot.exercise_roles,
                    required=slot.required,
                    base_sets=slot.base_sets,
                    base_reps=slot.base_reps,
                    base_rest_seconds=slot.base_rest_seconds,
                    base_rpe=slot.base_rpe,
                    progression_rule=slot.progression_rule,
                )
                for slot in template.slots
            ],
        )

    def _instance_dto(self, instance, recommendation: str) -> TodayProgramWorkoutDTO:
        return TodayProgramWorkoutDTO(
            program_id=instance.program_id,
            scheduled=True,
            recommendation=recommendation,
            week_number=instance.week_number,
            day_index=instance.day_index,
            instance_id=instance.id,
            status=instance.status.value,
            workout_plan_id=instance.actual_workout_plan_id,
        )

    def _today_instance_dto(self, instance, template) -> TodayProgramWorkoutDTO:
        recommendations = {
            ProgramWorkoutStatus.SCHEDULED: "generate_workout",
            ProgramWorkoutStatus.RESCHEDULED: "generate_workout",
            ProgramWorkoutStatus.GENERATED: "continue_workout",
            ProgramWorkoutStatus.STARTED: "continue_workout",
            ProgramWorkoutStatus.COMPLETED: "workout_completed",
            ProgramWorkoutStatus.SKIPPED: "workout_skipped",
        }
        return TodayProgramWorkoutDTO(
            program_id=instance.program_id,
            scheduled=True,
            recommendation=recommendations[instance.status],
            week_number=instance.week_number,
            day_index=instance.day_index,
            instance_id=instance.id,
            template=self._template_dto(template),
            status=instance.status.value,
            workout_plan_id=instance.actual_workout_plan_id,
        )
