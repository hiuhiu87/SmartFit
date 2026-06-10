import logging
from uuid import UUID, uuid4
from datetime import date, timedelta
from src.application.program.commands import CreateProgramCommand
from src.application.program.dto import (
    TrainingProgramDTO,
    ProgramTemplateDTO,
    ProgramSlotDTO,
    ProgramPhaseDTO,
)
from src.application.workout.commands import GenerateWorkoutCommand
from src.application.workout.use_cases import GenerateWorkoutUseCase
from src.domain.common.enums import Goal, EquipmentType
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.program.entities import (
    PreferredSplit,
    ProgramStatus,
    ProgramWorkoutStatus,
    TrainingProgram,
    ProgramGenerationStrategy,
)
from src.domain.program.repositories import ProgramRepository
from src.domain.user.repositories import UserRepository
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.workout.repositories import WorkoutRepository
from src.domain.progression.repositories import ProgressionRepository
from src.domain.program.program_template_factory import ProgramTemplateFactory
from src.domain.program.full_program_scheduler import FullProgramScheduler
from src.domain.program.periodization_policy import ProgramPeriodizationPolicy
from src.domain.program.program_workout_planner import ProgramWorkoutPlanner

logger = logging.getLogger(__name__)


class FullProgramGenerator:
    def __init__(
        self,
        program_repository: ProgramRepository,
        user_repository: UserRepository,
        exercise_repository: ExerciseRepository,
        workout_repository: WorkoutRepository,
        progression_repository: ProgressionRepository,
        template_factory: ProgramTemplateFactory,
        scheduler: FullProgramScheduler,
        periodization_policy: ProgramPeriodizationPolicy,
        workout_planner: ProgramWorkoutPlanner,
        workout_generation_use_case: GenerateWorkoutUseCase | None = None,
    ) -> None:
        self.program_repository = program_repository
        self.user_repository = user_repository
        self.exercise_repository = exercise_repository
        self.workout_repository = workout_repository
        self.progression_repository = progression_repository
        self.template_factory = template_factory
        self.scheduler = scheduler
        self.periodization_policy = periodization_policy
        self.workout_planner = workout_planner
        self.workout_generation_use_case = workout_generation_use_case

    async def generate_full_program(
        self, command: CreateProgramCommand
    ) -> TrainingProgramDTO:
        profile = await self.user_repository.get_profile(command.user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")
        if not 2 <= command.days_per_week <= 6:
            raise ValidationError("days_per_week must be between 2 and 6.")
        if not 1 <= command.duration_weeks <= 52:
            raise ValidationError("duration_weeks must be between 1 and 52.")

        start_date = command.start_date or date.today()
        program_id = uuid4()
        preferred_split = PreferredSplit(command.preferred_split)
        strategy = ProgramGenerationStrategy(command.generation_strategy)

        # 1. Create TrainingProgram
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
            generation_strategy=strategy,
            focus_areas=command.focus_areas,
        )

        # 2. Resolve Split & Templates
        templates = self.template_factory.create_weekly_structure(
            program_id=program.id,
            goal=program.goal,
            days_per_week=program.days_per_week,
            level=program.training_level,
            preferred_split=program.preferred_split,
            focus_areas=program.focus_areas,
            session_duration_minutes=program.session_duration_minutes,
            training_style=program.training_style,
        )
        program.templates = templates

        # 3. Create Phases
        phases = self.periodization_policy.create_phases(
            program_id=program.id,
            duration_weeks=program.duration_weeks,
            goal=program.goal,
            training_level=program.training_level,
            training_style=program.training_style,
        )
        program.phases = phases
        if phases:
            program.current_phase = phases[0].phase_type

        # 4. Generate weekly workout templates scheduled instances
        instances = self.scheduler.generate_instances(program, templates)
        program.instances = instances
        program.total_scheduled_workouts = len(instances)

        # 5. Upfront generation if generation_strategy is full_program.
        # AI generation is primary. Rule-based planning is only the fallback path.
        if strategy == ProgramGenerationStrategy.FULL_PROGRAM:
            equipment = [
                item.equipment_type.value
                for item in await self.user_repository.get_equipment(command.user_id)
            ]
            if not equipment:
                equipment = [EquipmentType.BODYWEIGHT.value]

            # Fetch active exercises
            allowed = await self.exercise_repository.find_allowed(
                equipment=equipment,
                focus_muscle=None,
                level=profile.training_level.value,
                limit=2000,
            )
            if not allowed:
                allowed = await self.exercise_repository.find_allowed(
                    equipment=[
                        EquipmentType.BODYWEIGHT.value,
                        EquipmentType.TREADMILL.value,
                        EquipmentType.RESISTANCE_BAND.value,
                    ],
                    focus_muscle=None,
                    level=profile.training_level.value,
                    limit=2000,
                )

            # Load progression history
            exercise_ids = [e.id for e in allowed]
            progression_histories = (
                await self.progression_repository.get_recent_performance_for_exercises(
                    user_id=command.user_id,
                    exercise_ids=exercise_ids,
                    limit_per_exercise=5,
                )
            )

            # Generate workout_plan for every instance
            for instance in instances:
                phase = next(
                    p
                    for p in phases
                    if p.start_week <= instance.week_number <= p.end_week
                )
                template = next(
                    t for t in templates if t.id == instance.program_workout_template_id
                )

                generated_with_ai_pipeline = await self._try_generate_with_ai_pipeline(
                    command=command,
                    program=program,
                    instance=instance,
                    template=template,
                    phase=phase,
                    equipment=equipment,
                )
                if generated_with_ai_pipeline:
                    continue

                workout_plan = self.workout_planner.generate_planned_workout(
                    template=template,
                    phase=phase,
                    user_profile=profile,
                    available_equipment=equipment,
                    exercises=allowed,
                    avoid_exercises=[],
                    recent_workouts=None,
                    progression_histories=progression_histories,
                    training_style=program.training_style,
                    target_date=instance.scheduled_date,
                )

                # Save plan
                await self.workout_repository.save_plan(workout_plan)

                instance.planned_workout_plan_id = workout_plan.id
                instance.actual_workout_plan_id = workout_plan.id

        # 6. Save program to DB
        saved_program = await self.program_repository.create_program(program)
        return self.to_dto(saved_program)

    async def _try_generate_with_ai_pipeline(
        self,
        *,
        command: CreateProgramCommand,
        program: TrainingProgram,
        instance,
        template,
        phase,
        equipment: list[str],
    ) -> bool:
        if self.workout_generation_use_case is None:
            return False

        try:
            result = await self.workout_generation_use_case.execute(
                GenerateWorkoutCommand(
                    user_id=instance.user_id,
                    target_date=instance.scheduled_date,
                    focus_muscle=template.focus_type,
                    available_time_minutes=template.estimated_duration_minutes,
                    workout_split=template.workout_type,
                    generation_mode=command.generation_mode,
                    equipment=equipment,
                    goal_override=program.goal,
                    training_style_override=program.training_style,
                    user_note=self._program_workout_note(template, phase),
                    allow_missing_readiness=True,
                )
            )
            instance.planned_workout_plan_id = result.workout_id
            instance.actual_workout_plan_id = result.workout_id
            return True
        except Exception as exc:
            logger.exception(
                "AI program workout generation failed; using rule-based fallback. "
                "program_id=%s instance_id=%s week=%s day=%s template=%s mode=%s error_type=%s error=%s",
                program.id,
                instance.id,
                instance.week_number,
                instance.day_index,
                template.focus_type,
                command.generation_mode,
                exc.__class__.__name__,
                exc,
            )
            return False

    def _program_workout_note(self, template, phase) -> str:
        slot_lines = [
            (
                f"{slot.slot_order}. {slot.slot_type}: patterns={','.join(slot.movement_patterns)}; "
                f"muscles={','.join(slot.primary_muscles)}; sets={slot.base_sets}; "
                f"reps={slot.base_reps}; rest={slot.base_rest_seconds}s; rpe={slot.base_rpe}"
            )
            for slot in template.slots
        ]
        return (
            "This is a pre-planned workout inside a multi-week training program. "
            "Follow the workout intent and slot blueprint closely. "
            f"Program day title: {template.title}. "
            f"Program focus: {template.focus_type}. "
            f"Workout type: {template.workout_type}. "
            f"Periodization phase: {phase.phase_type}. "
            "Prefer a clean PT-style plan with specific exercises, sensible order, "
            "and practical notes. Slot blueprint: " + " | ".join(slot_lines)
        )

    def to_dto(self, program: TrainingProgram) -> TrainingProgramDTO:
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
            generation_strategy=program.generation_strategy.value,
            current_phase=program.current_phase,
            total_scheduled_workouts=program.total_scheduled_workouts,
            completed_workouts_count=program.completed_workouts_count,
            weekly_structure=[
                ProgramTemplateDTO(
                    id=t.id,
                    day_index=t.day_index,
                    title=t.title,
                    focus_type=t.focus_type,
                    workout_type=t.workout_type,
                    estimated_duration_minutes=t.estimated_duration_minutes,
                    sequence_order=t.sequence_order,
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
                        for slot in t.slots
                    ],
                )
                for t in program.templates
            ],
            phases=[
                ProgramPhaseDTO(
                    id=p.id,
                    name=p.name,
                    phase_type=p.phase_type,
                    start_week=p.start_week,
                    end_week=p.end_week,
                    volume_multiplier=p.volume_multiplier,
                    intensity_multiplier=p.intensity_multiplier,
                    rpe_modifier=p.rpe_modifier,
                    is_deload=p.is_deload,
                    notes=p.notes,
                )
                for p in program.phases
            ],
        )
