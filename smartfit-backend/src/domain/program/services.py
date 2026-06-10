from datetime import date, timedelta
from uuid import UUID, uuid4

from src.domain.common.exceptions import ValidationError
from src.domain.program.entities import (
    PreferredSplit,
    ProgramTemplateSlot,
    ProgramWorkoutInstance,
    ProgramWorkoutStatus,
    ProgramWorkoutTemplate,
    TrainingProgram,
)
from src.domain.program.split_selection_policy import SplitSelectionPolicy


from src.domain.program.program_template_factory import ProgramTemplateFactory


class ProgramScheduler:
    DAY_OFFSETS = {
        2: [0, 3],
        3: [0, 2, 4],
        4: [0, 1, 3, 4],
        5: [0, 1, 2, 4, 5],
        6: [0, 1, 2, 3, 4, 5],
    }

    def calculate_position(
        self, program: TrainingProgram, target_date: date
    ) -> tuple[int, int | None]:
        elapsed = (target_date - program.start_date).days
        if elapsed < 0 or target_date > program.end_date:
            return 0, None
        week_number = (elapsed // 7) + 1
        offset = elapsed % 7
        offsets = self.DAY_OFFSETS[program.days_per_week]
        day_index = offsets.index(offset) if offset in offsets else None
        return week_number, day_index

    def scheduled_date(
        self, program: TrainingProgram, week_number: int, day_index: int
    ) -> date:
        return (
            program.start_date
            + timedelta(weeks=week_number - 1)
            + timedelta(days=self.DAY_OFFSETS[program.days_per_week][day_index])
        )

    def build_instance(
        self,
        program: TrainingProgram,
        template: ProgramWorkoutTemplate,
        target_date: date,
    ) -> ProgramWorkoutInstance:
        week_number, day_index = self.calculate_position(program, target_date)
        if day_index is None or day_index != template.day_index:
            raise ValidationError("No program workout is scheduled for this date.")
        return ProgramWorkoutInstance(
            id=uuid4(),
            program_id=program.id,
            program_workout_template_id=template.id,
            user_id=program.user_id,
            scheduled_date=target_date,
            week_number=week_number,
            day_index=day_index,
            actual_workout_plan_id=None,
            status=ProgramWorkoutStatus.SCHEDULED,
        )
