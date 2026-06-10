from datetime import date, timedelta
from uuid import UUID, uuid4
from src.domain.program.entities import ProgramWorkoutInstance, ProgramWorkoutTemplate, TrainingProgram, ProgramWorkoutStatus
from src.domain.common.exceptions import ValidationError

class FullProgramScheduler:
    DAY_OFFSETS = {
        2: [0, 3],              # Mon / Thu
        3: [0, 2, 4],           # Mon / Wed / Fri
        4: [0, 1, 3, 4],        # Mon / Tue / Thu / Fri
        5: [0, 1, 2, 4, 5],     # Mon / Tue / Wed / Fri / Sat
        6: [0, 1, 2, 3, 4, 5],  # Mon / Tue / Wed / Thu / Fri / Sat
    }

    def generate_instances(
        self, program: TrainingProgram, templates: list[ProgramWorkoutTemplate]
    ) -> list[ProgramWorkoutInstance]:
        instances = []
        days_per_week = program.days_per_week
        offsets = self.DAY_OFFSETS.get(days_per_week, list(range(days_per_week)))

        # Sort templates by day_index to align with offsets
        sorted_templates = sorted(templates, key=lambda t: t.day_index)

        for week in range(1, program.duration_weeks + 1):
            for day_idx, template in enumerate(sorted_templates):
                if day_idx >= len(offsets):
                    break
                offset_days = (week - 1) * 7 + offsets[day_idx]
                scheduled_date = program.start_date + timedelta(days=offset_days)
                
                instances.append(
                    ProgramWorkoutInstance(
                        id=uuid4(),
                        program_id=program.id,
                        program_workout_template_id=template.id,
                        user_id=program.user_id,
                        scheduled_date=scheduled_date,
                        week_number=week,
                        day_index=day_idx,
                        planned_workout_plan_id=None,
                        actual_workout_plan_id=None,
                        adjusted_workout_plan_id=None,
                        status=ProgramWorkoutStatus.SCHEDULED,
                        readiness_adjustment=None,
                        adjustment_reason=None,
                        original_scheduled_date=scheduled_date,
                        completed_at=None,
                    )
                )
        return instances

    def calculate_position(
        self, program: TrainingProgram, target_date: date
    ) -> tuple[int, int | None]:
        elapsed = (target_date - program.start_date).days
        if elapsed < 0 or target_date > program.end_date:
            return 0, None
        week_number = (elapsed // 7) + 1
        offset = elapsed % 7
        offsets = self.DAY_OFFSETS.get(program.days_per_week, list(range(program.days_per_week)))
        day_index = offsets.index(offset) if offset in offsets else None
        return week_number, day_index

    def scheduled_date(
        self, program: TrainingProgram, week_number: int, day_index: int
    ) -> date:
        offsets = self.DAY_OFFSETS.get(program.days_per_week, list(range(program.days_per_week)))
        if day_index >= len(offsets):
            raise ValidationError("Invalid day index for program days per week.")
        return (
            program.start_date
            + timedelta(weeks=week_number - 1)
            + timedelta(days=offsets[day_index])
        )
