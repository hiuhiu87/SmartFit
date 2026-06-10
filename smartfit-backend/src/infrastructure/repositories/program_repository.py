from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.domain.program.entities import (
    PreferredSplit,
    ProgramStatus,
    ProgramTemplateSlot,
    ProgramWorkoutInstance,
    ProgramWorkoutStatus,
    ProgramWorkoutTemplate,
    TrainingProgram,
    ProgramPhase,
    ProgramGenerationStrategy,
)
from src.domain.program.repositories import ProgramRepository
from src.infrastructure.database.models.program_model import (
    ProgramTemplateSlotModel,
    ProgramWorkoutInstanceModel,
    ProgramWorkoutTemplateModel,
    TrainingProgramModel,
    ProgramPhaseModel,
)


class SQLModelProgramRepository(ProgramRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_program(self, program: TrainingProgram) -> TrainingProgram:
        now = datetime.now(timezone.utc)
        active_result = await self.session.execute(
            select(TrainingProgramModel).where(
                TrainingProgramModel.user_id == program.user_id,
                TrainingProgramModel.status == ProgramStatus.ACTIVE.value,
            )
        )
        for active in active_result.scalars().all():
            active.status = ProgramStatus.CANCELLED.value
            active.updated_at = now

        model = TrainingProgramModel(
            id=program.id,
            user_id=program.user_id,
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
            generation_strategy=program.generation_strategy.value,
            current_phase=program.current_phase,
            total_scheduled_workouts=program.total_scheduled_workouts,
            completed_workouts_count=program.completed_workouts_count,
            focus_areas=program.focus_areas,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()

        # Save phases
        phase_models = [
            ProgramPhaseModel(
                id=phase.id,
                program_id=phase.program_id,
                name=phase.name,
                phase_type=phase.phase_type,
                start_week=phase.start_week,
                end_week=phase.end_week,
                volume_multiplier=phase.volume_multiplier,
                intensity_multiplier=phase.intensity_multiplier,
                rpe_modifier=phase.rpe_modifier,
                is_deload=phase.is_deload,
                notes=phase.notes,
                created_at=now,
                updated_at=now,
            )
            for phase in program.phases
        ]
        if phase_models:
            self.session.add_all(phase_models)
            await self.session.flush()

        template_models = [
            ProgramWorkoutTemplateModel(
                id=template.id,
                program_id=template.program_id,
                day_index=template.day_index,
                title=template.title,
                focus_type=template.focus_type,
                workout_type=template.workout_type,
                estimated_duration_minutes=template.estimated_duration_minutes,
                sequence_order=template.sequence_order,
            )
            for template in program.templates
        ]
        self.session.add_all(template_models)
        await self.session.flush()

        for template in program.templates:
            for slot in template.slots:
                self.session.add(
                    ProgramTemplateSlotModel(
                        id=slot.id,
                        program_workout_template_id=slot.program_workout_template_id,
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
                )
        await self.session.flush()

        # Save instances if present
        instances = getattr(program, "instances", [])
        if instances:
            instance_models = [
                ProgramWorkoutInstanceModel(
                    id=inst.id,
                    program_id=inst.program_id,
                    program_workout_template_id=inst.program_workout_template_id,
                    user_id=inst.user_id,
                    scheduled_date=inst.scheduled_date,
                    week_number=inst.week_number,
                    day_index=inst.day_index,
                    planned_workout_plan_id=inst.planned_workout_plan_id,
                    actual_workout_plan_id=inst.actual_workout_plan_id,
                    adjusted_workout_plan_id=inst.adjusted_workout_plan_id,
                    status=inst.status.value,
                    readiness_adjustment=inst.readiness_adjustment,
                    adjustment_reason=inst.adjustment_reason,
                    original_scheduled_date=inst.original_scheduled_date,
                    completed_at=inst.completed_at,
                    created_at=now,
                    updated_at=now,
                )
                for inst in instances
            ]
            self.session.add_all(instance_models)
            await self.session.flush()

        program.created_at = now
        program.updated_at = now
        return program

    async def get_active_program(self, user_id: UUID) -> TrainingProgram | None:
        result = await self.session.execute(
            select(TrainingProgramModel)
            .where(
                TrainingProgramModel.user_id == user_id,
                TrainingProgramModel.status == ProgramStatus.ACTIVE.value,
            )
            .order_by(TrainingProgramModel.created_at.desc())
        )
        model = result.scalars().first()
        return await self._to_program(model) if model else None

    async def get_program_by_id(
        self, program_id: UUID, user_id: UUID | None = None
    ) -> TrainingProgram | None:
        statement = select(TrainingProgramModel).where(
            TrainingProgramModel.id == program_id
        )
        if user_id is not None:
            statement = statement.where(TrainingProgramModel.user_id == user_id)
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        return await self._to_program(model) if model else None

    async def list_program_workout_templates(
        self, program_id: UUID
    ) -> list[ProgramWorkoutTemplate]:
        result = await self.session.execute(
            select(ProgramWorkoutTemplateModel)
            .where(ProgramWorkoutTemplateModel.program_id == program_id)
            .order_by(ProgramWorkoutTemplateModel.sequence_order)
        )
        templates = []
        for model in result.scalars().all():
            slots_result = await self.session.execute(
                select(ProgramTemplateSlotModel)
                .where(ProgramTemplateSlotModel.program_workout_template_id == model.id)
                .order_by(ProgramTemplateSlotModel.slot_order)
            )
            templates.append(
                ProgramWorkoutTemplate(
                    id=model.id,
                    program_id=model.program_id,
                    day_index=model.day_index,
                    title=model.title,
                    focus_type=model.focus_type,
                    workout_type=model.workout_type,
                    estimated_duration_minutes=model.estimated_duration_minutes,
                    sequence_order=model.sequence_order,
                    slots=[
                        self._slot_to_domain(slot)
                        for slot in slots_result.scalars().all()
                    ],
                )
            )
        return templates

    async def get_today_instance(
        self, program_id: UUID, scheduled_date: date
    ) -> ProgramWorkoutInstance | None:
        result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(
                ProgramWorkoutInstanceModel.program_id == program_id,
                ProgramWorkoutInstanceModel.scheduled_date == scheduled_date,
            )
        )
        model = result.scalars().first()
        return self._instance_to_domain(model) if model else None

    async def create_or_get_today_instance(
        self, instance: ProgramWorkoutInstance
    ) -> ProgramWorkoutInstance:
        result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(
                ProgramWorkoutInstanceModel.program_id == instance.program_id,
                ProgramWorkoutInstanceModel.week_number == instance.week_number,
                ProgramWorkoutInstanceModel.day_index == instance.day_index,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return self._instance_to_domain(existing)
        now = datetime.now(timezone.utc)
        model = ProgramWorkoutInstanceModel(
            id=instance.id,
            program_id=instance.program_id,
            program_workout_template_id=instance.program_workout_template_id,
            user_id=instance.user_id,
            scheduled_date=instance.scheduled_date,
            week_number=instance.week_number,
            day_index=instance.day_index,
            planned_workout_plan_id=instance.planned_workout_plan_id,
            actual_workout_plan_id=instance.actual_workout_plan_id,
            adjusted_workout_plan_id=instance.adjusted_workout_plan_id,
            status=instance.status.value,
            readiness_adjustment=instance.readiness_adjustment,
            adjustment_reason=instance.adjustment_reason,
            original_scheduled_date=instance.original_scheduled_date,
            completed_at=instance.completed_at,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return self._instance_to_domain(model)

    async def get_instance_by_id(
        self, instance_id: UUID, user_id: UUID
    ) -> ProgramWorkoutInstance | None:
        result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(
                ProgramWorkoutInstanceModel.id == instance_id,
                ProgramWorkoutInstanceModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._instance_to_domain(model) if model else None

    async def get_instance_by_workout_plan_id(
        self, workout_plan_id: UUID
    ) -> ProgramWorkoutInstance | None:
        result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(
                (ProgramWorkoutInstanceModel.actual_workout_plan_id == workout_plan_id) |
                (ProgramWorkoutInstanceModel.planned_workout_plan_id == workout_plan_id) |
                (ProgramWorkoutInstanceModel.adjusted_workout_plan_id == workout_plan_id)
            )
        )
        model = result.scalar_one_or_none()
        return self._instance_to_domain(model) if model else None

    async def link_workout_plan_to_instance(
        self,
        instance_id: UUID,
        workout_plan_id: UUID,
        readiness_adjustment: str | None,
        planned_workout_plan_id: UUID | None = None,
        adjusted_workout_plan_id: UUID | None = None,
        adjustment_reason: str | None = None,
    ) -> ProgramWorkoutInstance:
        model = await self._instance_model(instance_id)
        model.actual_workout_plan_id = workout_plan_id
        if planned_workout_plan_id is not None:
            model.planned_workout_plan_id = planned_workout_plan_id
        if adjusted_workout_plan_id is not None:
            model.adjusted_workout_plan_id = adjusted_workout_plan_id
        if adjustment_reason is not None:
            model.adjustment_reason = adjustment_reason
        model.status = ProgramWorkoutStatus.GENERATED.value
        model.readiness_adjustment = readiness_adjustment
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return self._instance_to_domain(model)

    async def update_instance_status(
        self,
        instance_id: UUID,
        status: ProgramWorkoutStatus,
        scheduled_date: date | None = None,
    ) -> ProgramWorkoutInstance:
        model = await self._instance_model(instance_id)
        model.status = status.value
        if scheduled_date is not None:
            model.scheduled_date = scheduled_date
        if status == ProgramWorkoutStatus.COMPLETED:
            model.completed_at = datetime.now(timezone.utc)
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()

        # Update program's completed count if program exists
        if status == ProgramWorkoutStatus.COMPLETED:
            prog_result = await self.session.execute(
                select(TrainingProgramModel).where(TrainingProgramModel.id == model.program_id)
            )
            prog = prog_result.scalar_one_or_none()
            if prog:
                prog.completed_workouts_count += 1
                prog.updated_at = datetime.now(timezone.utc)
                await self.session.flush()

        return self._instance_to_domain(model)

    async def update_program_progress(
        self, program_id: UUID, current_week: int, current_day_index: int
    ) -> None:
        result = await self.session.execute(
            select(TrainingProgramModel).where(TrainingProgramModel.id == program_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.current_week = current_week
            model.current_day_index = current_day_index
            model.updated_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def _to_program(self, model: TrainingProgramModel) -> TrainingProgram:
        # Load phases
        phases_result = await self.session.execute(
            select(ProgramPhaseModel)
            .where(ProgramPhaseModel.program_id == model.id)
            .order_by(ProgramPhaseModel.start_week)
        )
        phases = [
            ProgramPhase(
                id=p.id,
                program_id=p.program_id,
                name=p.name,
                phase_type=p.phase_type,
                start_week=p.start_week,
                end_week=p.end_week,
                volume_multiplier=p.volume_multiplier,
                intensity_multiplier=p.intensity_multiplier,
                rpe_modifier=p.rpe_modifier,
                is_deload=p.is_deload,
                notes=p.notes,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in phases_result.scalars().all()
        ]

        # Load instances
        instances_result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(ProgramWorkoutInstanceModel.program_id == model.id)
        )
        instances = [self._instance_to_domain(inst) for inst in instances_result.scalars().all()]

        program = TrainingProgram(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            goal=model.goal,
            training_level=model.training_level,
            training_style=model.training_style,
            duration_weeks=model.duration_weeks,
            days_per_week=model.days_per_week,
            session_duration_minutes=model.session_duration_minutes,
            preferred_split=PreferredSplit(model.preferred_split),
            status=ProgramStatus(model.status),
            start_date=model.start_date,
            end_date=model.end_date,
            current_week=model.current_week,
            current_day_index=model.current_day_index,
            generation_mode=model.generation_mode,
            generation_strategy=ProgramGenerationStrategy(model.generation_strategy),
            current_phase=model.current_phase,
            total_scheduled_workouts=model.total_scheduled_workouts,
            completed_workouts_count=model.completed_workouts_count,
            focus_areas=model.focus_areas,
            templates=await self.list_program_workout_templates(model.id),
            phases=phases,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        program.instances = instances
        return program

    async def _instance_model(self, instance_id: UUID) -> ProgramWorkoutInstanceModel:
        result = await self.session.execute(
            select(ProgramWorkoutInstanceModel).where(
                ProgramWorkoutInstanceModel.id == instance_id
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Program workout instance not found.")
        return model

    def _slot_to_domain(self, model: ProgramTemplateSlotModel) -> ProgramTemplateSlot:
        return ProgramTemplateSlot(
            id=model.id,
            program_workout_template_id=model.program_workout_template_id,
            slot_order=model.slot_order,
            slot_type=model.slot_type,
            movement_patterns=model.movement_patterns,
            primary_muscles=model.primary_muscles,
            exercise_roles=model.exercise_roles,
            required=model.required,
            base_sets=model.base_sets,
            base_reps=model.base_reps,
            base_rest_seconds=model.base_rest_seconds,
            base_rpe=model.base_rpe,
            progression_rule=model.progression_rule,
        )

    def _instance_to_domain(
        self, model: ProgramWorkoutInstanceModel
    ) -> ProgramWorkoutInstance:
        return ProgramWorkoutInstance(
            id=model.id,
            program_id=model.program_id,
            program_workout_template_id=model.program_workout_template_id,
            user_id=model.user_id,
            scheduled_date=model.scheduled_date,
            week_number=model.week_number,
            day_index=model.day_index,
            planned_workout_plan_id=model.planned_workout_plan_id,
            actual_workout_plan_id=model.actual_workout_plan_id,
            adjusted_workout_plan_id=model.adjusted_workout_plan_id,
            status=ProgramWorkoutStatus(model.status),
            readiness_adjustment=model.readiness_adjustment,
            adjustment_reason=model.adjustment_reason,
            original_scheduled_date=model.original_scheduled_date,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
