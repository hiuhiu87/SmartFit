from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.program.entities import (
    ProgramWorkoutInstance,
    ProgramWorkoutStatus,
    ProgramWorkoutTemplate,
    TrainingProgram,
)


class ProgramRepository(ABC):
    @abstractmethod
    async def create_program(self, program: TrainingProgram) -> TrainingProgram:
        raise NotImplementedError

    @abstractmethod
    async def get_active_program(self, user_id: UUID) -> TrainingProgram | None:
        raise NotImplementedError

    @abstractmethod
    async def get_program_by_id(
        self, program_id: UUID, user_id: UUID | None = None
    ) -> TrainingProgram | None:
        raise NotImplementedError

    @abstractmethod
    async def list_program_workout_templates(
        self, program_id: UUID
    ) -> list[ProgramWorkoutTemplate]:
        raise NotImplementedError

    @abstractmethod
    async def get_today_instance(
        self, program_id: UUID, scheduled_date: date
    ) -> ProgramWorkoutInstance | None:
        raise NotImplementedError

    @abstractmethod
    async def create_or_get_today_instance(
        self, instance: ProgramWorkoutInstance
    ) -> ProgramWorkoutInstance:
        raise NotImplementedError

    @abstractmethod
    async def get_instance_by_id(
        self, instance_id: UUID, user_id: UUID
    ) -> ProgramWorkoutInstance | None:
        raise NotImplementedError

    @abstractmethod
    async def get_instance_by_workout_plan_id(
        self, workout_plan_id: UUID
    ) -> ProgramWorkoutInstance | None:
        raise NotImplementedError

    @abstractmethod
    async def link_workout_plan_to_instance(
        self,
        instance_id: UUID,
        workout_plan_id: UUID,
        readiness_adjustment: str | None,
    ) -> ProgramWorkoutInstance:
        raise NotImplementedError

    @abstractmethod
    async def update_instance_status(
        self,
        instance_id: UUID,
        status: ProgramWorkoutStatus,
        scheduled_date: date | None = None,
    ) -> ProgramWorkoutInstance:
        raise NotImplementedError

    @abstractmethod
    async def update_program_progress(
        self, program_id: UUID, current_week: int, current_day_index: int
    ) -> None:
        raise NotImplementedError
