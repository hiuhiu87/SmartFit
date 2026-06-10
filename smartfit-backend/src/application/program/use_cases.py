from datetime import date, timedelta, datetime
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
    ProgramCalendarDayDTO,
    ProgramPhaseDTO,
)
from src.application.program.generator import ProgramWorkoutGenerator
from src.application.workout.dto import WorkoutPlanDTO, WorkoutExerciseDTO, WorkoutSetLogDTO
from src.domain.common.exceptions import NotFoundError, ValidationError
from src.domain.common.enums import Goal, EquipmentType
from src.domain.program.entities import (
    PreferredSplit,
    ProgramStatus,
    ProgramWorkoutStatus,
    TrainingProgram,
    ProgramWorkoutInstance,
    ProgramCalendarDay,
    ProgramGenerationStrategy,
    ProgramAdjustmentType,
)
from src.domain.program.repositories import ProgramRepository
from src.domain.user.repositories import UserRepository
from src.domain.exercise.repositories import ExerciseRepository
from src.domain.workout.repositories import WorkoutRepository
from src.domain.readiness.repositories import ReadinessRepository
from src.domain.progression.repositories import ProgressionRepository
from src.domain.program.periodization_policy import ProgramPeriodizationPolicy
from src.domain.program.program_workout_planner import ProgramWorkoutPlanner
from src.application.program.full_program_generator import FullProgramGenerator
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise


class ProgramService:
    def __init__(
        self,
        repository: ProgramRepository,
        user_repository: UserRepository,
        template_factory,
        scheduler,
        workout_generator: ProgramWorkoutGenerator,
        full_generator: FullProgramGenerator,
        workout_repository: WorkoutRepository,
        readiness_repository: ReadinessRepository,
        exercise_repository: ExerciseRepository,
        progression_repository: ProgressionRepository,
        periodization_policy: ProgramPeriodizationPolicy,
        workout_planner: ProgramWorkoutPlanner,
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository
        self.template_factory = template_factory
        self.scheduler = scheduler
        self.workout_generator = workout_generator
        self.full_generator = full_generator
        self.workout_repository = workout_repository
        self.readiness_repository = readiness_repository
        self.exercise_repository = exercise_repository
        self.progression_repository = progression_repository
        self.periodization_policy = periodization_policy
        self.workout_planner = workout_planner

    async def create_program(self, command: CreateProgramCommand) -> TrainingProgramDTO:
        return await self.full_generator.generate_full_program(command)

    async def get_active_program(self, user_id: UUID) -> TrainingProgramDTO:
        program = await self.repository.get_active_program(user_id)
        if program is None:
            raise NotFoundError("Active training program not found.")
        return self.full_generator.to_dto(program)

    async def get_calendar(
        self, user_id: UUID, from_date: date | None = None, to_date: date | None = None
    ) -> list[ProgramCalendarDayDTO]:
        program = await self.repository.get_active_program(user_id)
        if program is None:
            raise NotFoundError("Active training program not found.")

        instances = getattr(program, "instances", [])
        if from_date is not None:
            instances = [inst for inst in instances if inst.scheduled_date >= from_date]
        if to_date is not None:
            instances = [inst for inst in instances if inst.scheduled_date <= to_date]

        calendar_days = []
        for inst in sorted(instances, key=lambda i: i.scheduled_date):
            template = next(
                (t for t in program.templates if t.id == inst.program_workout_template_id),
                None,
            )
            title = template.title if template else "Rest Day"
            focus_type = template.focus_type if template else "recovery"

            calendar_days.append(
                ProgramCalendarDayDTO(
                    date=inst.scheduled_date,
                    week_number=inst.week_number,
                    day_index=inst.day_index,
                    title=title,
                    focus_type=focus_type,
                    status=inst.status.value,
                    workout_plan_id=inst.actual_workout_plan_id,
                    planned_workout_plan_id=inst.planned_workout_plan_id,
                )
            )
        return calendar_days

    async def get_week(self, program_id: UUID, user_id: UUID, week_number: int) -> dict:
        program = await self.repository.get_program_by_id(program_id, user_id)
        if program is None:
            raise NotFoundError("Training program not found.")

        phase_type = "foundation"
        for p in program.phases:
            if p.start_week <= week_number <= p.end_week:
                phase_type = p.phase_type
                break

        instances = [
            inst for inst in getattr(program, "instances", [])
            if inst.week_number == week_number
        ]
        
        workouts_summary = []
        for inst in sorted(instances, key=lambda i: i.day_index):
            template = next(
                (t for t in program.templates if t.id == inst.program_workout_template_id),
                None,
            )
            title = template.title if template else "Workout"
            focus_type = template.focus_type if template else "recovery"
            workouts_summary.append(
                {
                    "instance_id": inst.id,
                    "title": title,
                    "focus_type": focus_type,
                    "status": inst.status.value,
                    "planned_workout_plan_id": inst.planned_workout_plan_id,
                    "actual_workout_plan_id": inst.actual_workout_plan_id,
                    "adjusted_workout_plan_id": inst.adjusted_workout_plan_id,
                }
            )

        return {
            "phase": phase_type,
            "workouts": workouts_summary,
        }

    async def get_today(
        self, user_id: UUID, target_date: date
    ) -> dict:
        program = await self.repository.get_active_program(user_id)
        if program is None:
            raise NotFoundError("Active training program not found.")

        instance = next(
            (inst for inst in getattr(program, "instances", []) if inst.scheduled_date == target_date),
            None,
        )

        if instance is None:
            week_number, _ = self.scheduler.calculate_position(program, target_date)
            phase_type = "recovery"
            if week_number:
                for p in program.phases:
                    if p.start_week <= week_number <= p.end_week:
                        phase_type = p.phase_type
                        break
            return {
                "program_id": program.id,
                "week_number": week_number or 1,
                "day_index": None,
                "phase": phase_type,
                "scheduled": False,
                "instance_id": None,
                "template": None,
                "status": None,
                "workout_plan_id": None,
                "scheduled_workout": None,
                "recommendation": {
                    "action": "rest_day",
                    "readiness_adjustment": "rest",
                    "message": "Today is a rest day."
                }
            }

        phase_type = "foundation"
        for p in program.phases:
            if p.start_week <= instance.week_number <= p.end_week:
                phase_type = p.phase_type
                break

        template = next(
            (t for t in program.templates if t.id == instance.program_workout_template_id),
            None,
        )
        title = template.title if template else "Workout"
        focus_type = template.focus_type if template else "recovery"

        # Load readiness score
        readiness_score = 100
        readiness_rec = "train_normal"
        try:
            readiness = await self.readiness_repository.get_by_date(user_id, target_date)
            if readiness:
                readiness_score = readiness.score
                readiness_rec = readiness.recommendation
        except Exception:
            pass

        # Calculate adjustments
        if instance.status == ProgramWorkoutStatus.COMPLETED:
            action = "workout_completed"
            readiness_adjustment = "normal_volume"
            message = "Workout completed!"
        elif instance.status == ProgramWorkoutStatus.SKIPPED:
            action = "workout_skipped"
            readiness_adjustment = "normal_volume"
            message = "Workout was skipped."
        elif instance.adjusted_workout_plan_id is not None:
            action = "open_adjusted_workout"
            readiness_adjustment = instance.readiness_adjustment or "normal_volume"
            message = instance.adjustment_reason or "Your workout has been adjusted."
        elif readiness_score < 45 or readiness_rec in ("recovery", "reduce_volume", "reduce_load", "rest"):
            action = "adjust_workout"
            readiness_adjustment = "reduce_volume" if readiness_rec == "reduce_volume" else "recovery_substitution"
            message = "Your readiness is low today. We recommend adjusting your workout."
        else:
            action = "open_planned_workout"
            readiness_adjustment = "normal_volume"
            message = f"Today is {title}. Your readiness supports normal training."

        return {
            "program_id": program.id,
            "week_number": instance.week_number,
            "day_index": instance.day_index,
            "phase": phase_type,
            "scheduled": True,
            "instance_id": instance.id,
            "template": self._template_dto(template) if template else None,
            "status": instance.status.value,
            "workout_plan_id": instance.actual_workout_plan_id or instance.planned_workout_plan_id,
            "scheduled_workout": {
                "instance_id": instance.id,
                "title": title,
                "focus_type": focus_type,
                "status": instance.status.value,
                "planned_workout_plan_id": instance.planned_workout_plan_id,
            },
            "recommendation": {
                "action": action,
                "readiness_adjustment": readiness_adjustment,
                "message": message,
            }
        }

    async def open_planned_workout(self, user_id: UUID, instance_id: UUID) -> WorkoutPlanDTO:
        instance = await self.repository.get_instance_by_id(instance_id, user_id)
        if instance is None:
            raise NotFoundError("Program workout instance not found.")

        if instance.planned_workout_plan_id is None:
            # Generate dynamically for structure_only programs
            program = await self.repository.get_program_by_id(instance.program_id, user_id)
            if program is None:
                raise NotFoundError("Training program not found.")
            
            profile = await self.user_repository.get_profile(user_id)
            if profile is None:
                raise NotFoundError("User profile not found.")

            equipment = [
                item.equipment_type.value
                for item in await self.user_repository.get_equipment(user_id)
            ]
            if not equipment:
                equipment = [EquipmentType.BODYWEIGHT.value]

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

            exercise_ids = [e.id for e in allowed]
            progression_histories = await self.progression_repository.get_recent_performance_for_exercises(
                user_id=user_id,
                exercise_ids=exercise_ids,
                limit_per_exercise=5,
            )

            phase = next(
                p for p in program.phases
                if p.start_week <= instance.week_number <= p.end_week
            )
            template = next(
                t for t in program.templates
                if t.id == instance.program_workout_template_id
            )

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
            await self.workout_repository.save_plan(workout_plan)
            await self.repository.link_workout_plan_to_instance(
                instance_id=instance.id,
                workout_plan_id=workout_plan.id,
                readiness_adjustment=None,
                planned_workout_plan_id=workout_plan.id,
            )
            instance.planned_workout_plan_id = workout_plan.id
            instance.actual_workout_plan_id = workout_plan.id

        plan = await self.workout_repository.get_plan_detail_by_id(instance.planned_workout_plan_id)
        if plan is None:
            raise NotFoundError("Planned workout plan not found.")
        return self._to_plan_dto(plan)

    async def adjust_today_workout(
        self, user_id: UUID, instance_id: UUID, adjustment_type: str, reason: str | None = None
    ) -> WorkoutPlanDTO:
        instance = await self.repository.get_instance_by_id(instance_id, user_id)
        if instance is None:
            raise NotFoundError("Program workout instance not found.")

        if instance.planned_workout_plan_id is None:
            raise ValidationError("Planned workout plan not found. Generate the planned workout first.")

        if instance.adjusted_workout_plan_id is not None:
            plan = await self.workout_repository.get_plan_detail_by_id(instance.adjusted_workout_plan_id)
            if plan is None:
                raise NotFoundError("Adjusted workout plan not found.")
            return self._to_plan_dto(plan)

        original_plan = await self.workout_repository.get_plan_detail_by_id(instance.planned_workout_plan_id)
        if original_plan is None:
            raise NotFoundError("Planned workout plan not found.")

        adjusted_id = uuid4()
        adjusted_exercises = []
        for index, item in enumerate(original_plan.exercises):
            target_sets = item.target_sets
            target_reps = item.target_reps
            target_rpe = item.target_rpe

            if adjustment_type == ProgramAdjustmentType.REDUCED_VOLUME.value:
                target_sets = max(1, target_sets - 1)
            elif adjustment_type in (ProgramAdjustmentType.RECOVERY_SUBSTITUTION.value, ProgramAdjustmentType.DELOAD.value):
                target_sets = max(1, round(target_sets * 0.6))
                target_rpe = max(1, target_rpe - 2)

            adjusted_exercises.append(
                WorkoutPlanExercise(
                    id=uuid4(),
                    workout_plan_id=adjusted_id,
                    exercise_id=item.exercise_id,
                    order_index=item.order_index,
                    target_sets=target_sets,
                    target_reps=target_reps,
                    target_rpe=target_rpe,
                    target_weight=item.target_weight,
                    rest_seconds=item.rest_seconds,
                    notes=f"Adjusted: {adjustment_type}. {item.notes or ''}",
                    name=item.name,
                    primary_muscle=item.primary_muscle,
                    equipment=item.equipment,
                )
            )

        title = f"{original_plan.title} (Adjusted - {adjustment_type.replace('_', ' ').title()})"
        adjusted_plan = WorkoutPlan(
            id=adjusted_id,
            user_id=user_id,
            target_date=original_plan.target_date,
            title=title,
            goal=original_plan.goal,
            focus=original_plan.focus,
            status=original_plan.status,
            source=original_plan.source,
            estimated_duration_minutes=original_plan.estimated_duration_minutes,
            readiness_score=original_plan.readiness_score,
            decision=adjustment_type,
            ai_reasoning_summary=reason or f"Adjusted via {adjustment_type} due to readiness.",
            safety_note=original_plan.safety_note,
            exercises=adjusted_exercises,
        )

        await self.workout_repository.save_plan(adjusted_plan)
        await self.repository.link_workout_plan_to_instance(
            instance_id=instance.id,
            workout_plan_id=adjusted_plan.id,
            readiness_adjustment=adjustment_type,
            adjusted_workout_plan_id=adjusted_plan.id,
            adjustment_reason=reason or f"Adjusted due to readiness ({adjustment_type}).",
        )

        return self._to_plan_dto(adjusted_plan)

    async def regenerate_program(self, program_id: UUID, user_id: UUID, from_week: int) -> TrainingProgramDTO:
        program = await self.repository.get_program_by_id(program_id, user_id)
        if program is None:
            raise NotFoundError("Training program not found.")

        instances = [inst for inst in getattr(program, "instances", []) if inst.week_number >= from_week]
        if any(inst.status == ProgramWorkoutStatus.COMPLETED for inst in instances):
            raise ValidationError("Cannot regenerate program from a week with completed workouts.")

        profile = await self.user_repository.get_profile(user_id)
        if profile is None:
            raise NotFoundError("User profile not found.")

        equipment = [
            item.equipment_type.value
            for item in await self.user_repository.get_equipment(user_id)
        ]
        if not equipment:
            equipment = [EquipmentType.BODYWEIGHT.value]

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

        exercise_ids = [e.id for e in allowed]
        progression_histories = await self.progression_repository.get_recent_performance_for_exercises(
            user_id=user_id,
            exercise_ids=exercise_ids,
            limit_per_exercise=5,
        )

        for inst in instances:
            phase = next(
                p for p in program.phases
                if p.start_week <= inst.week_number <= p.end_week
            )
            template = next(
                t for t in program.templates
                if t.id == inst.program_workout_template_id
            )

            new_plan = self.workout_planner.generate_planned_workout(
                template=template,
                phase=phase,
                user_profile=profile,
                available_equipment=equipment,
                exercises=allowed,
                avoid_exercises=[],
                recent_workouts=None,
                progression_histories=progression_histories,
                training_style=program.training_style,
                target_date=inst.scheduled_date,
            )
            await self.workout_repository.save_plan(new_plan)
            await self.repository.link_workout_plan_to_instance(
                instance_id=inst.id,
                workout_plan_id=new_plan.id,
                readiness_adjustment=None,
                planned_workout_plan_id=new_plan.id,
            )
            inst.planned_workout_plan_id = new_plan.id
            inst.actual_workout_plan_id = new_plan.id
            inst.adjusted_workout_plan_id = None
            inst.readiness_adjustment = None
            inst.status = ProgramWorkoutStatus.SCHEDULED

        updated_program = await self.repository.get_program_by_id(program_id, user_id)
        return self.full_generator.to_dto(updated_program)

    async def generate_today(
        self, command: GenerateTodayProgramWorkoutCommand
    ) -> WorkoutPlanDTO:
        today = await self.get_today(command.user_id, command.target_date)
        
        sw = today.get("scheduled_workout")
        if sw and sw.get("instance_id"):
            instance_id = sw["instance_id"]
            
            rec = today.get("recommendation", {})
            action = rec.get("action")
            adjustment_type = rec.get("readiness_adjustment")
            
            if action == "adjust_workout":
                plan_dto = await self.adjust_today_workout(
                    user_id=command.user_id,
                    instance_id=instance_id,
                    adjustment_type=adjustment_type,
                    reason=rec.get("message"),
                )
                await self.repository.update_instance_status(instance_id, ProgramWorkoutStatus.GENERATED)
                return plan_dto
            else:
                await self.repository.update_instance_status(instance_id, ProgramWorkoutStatus.GENERATED)
                return await self.open_planned_workout(command.user_id, instance_id)

        raise ValidationError("No program workout is scheduled for today.")

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
        # Construct TodayProgramWorkoutDTO for return
        return TodayProgramWorkoutDTO(
            program_id=instance.program_id,
            scheduled=True,
            recommendation="workout_skipped",
            week_number=instance.week_number,
            day_index=instance.day_index,
            instance_id=instance.id,
            status=instance.status.value,
            workout_plan_id=instance.actual_workout_plan_id or instance.planned_workout_plan_id,
        )

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
        return TodayProgramWorkoutDTO(
            program_id=instance.program_id,
            scheduled=True,
            recommendation="workout_rescheduled",
            week_number=instance.week_number,
            day_index=instance.day_index,
            instance_id=instance.id,
            status=instance.status.value,
            workout_plan_id=instance.actual_workout_plan_id or instance.planned_workout_plan_id,
        )

    def _to_plan_dto(self, plan: WorkoutPlan) -> WorkoutPlanDTO:
        td = plan.decision
        if td == "recovery_substitution":
            td = "recovery"
        return WorkoutPlanDTO(
            workout_id=plan.id,
            workout_log_id=plan.workout_log_id,
            title=plan.title,
            focus_muscle=plan.focus.value,
            estimated_duration_minutes=plan.estimated_duration_minutes,
            training_decision=td,
            ai_reasoning_summary=plan.ai_reasoning_summary,
            safety_note=plan.safety_note,
            status=plan.status.value,
            source=plan.source.value,
            exercises=[
                WorkoutExerciseDTO(
                    workout_plan_exercise_id=item.id,
                    exercise_id=item.exercise_id,
                    name=item.name or "Unknown Exercise",
                    order_index=item.order_index,
                    primary_muscle=item.primary_muscle or "full_body",
                    equipment=item.equipment or "bodyweight",
                    target_sets=item.target_sets,
                    target_reps=item.target_reps,
                    target_weight=item.target_weight,
                    rest_seconds=item.rest_seconds,
                    target_rpe=item.target_rpe,
                    notes=item.notes,
                    logged_sets=[
                        WorkoutSetLogDTO(
                            set_log_id=set_log.id,
                            set_number=set_log.set_number,
                            weight=set_log.weight_kg,
                            reps=set_log.reps_completed,
                            rpe=set_log.rpe,
                            completed=set_log.completed,
                        )
                        for set_log in item.logged_sets
                    ],
                )
                for item in plan.exercises
            ],
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
