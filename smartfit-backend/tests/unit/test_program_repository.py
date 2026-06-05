from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.domain.program.entities import PreferredSplit, ProgramStatus, TrainingProgram
from src.domain.program.services import ProgramTemplateFactory
from src.infrastructure.database.models.program_model import (
    ProgramTemplateSlotModel,
    ProgramWorkoutTemplateModel,
    TrainingProgramModel,
)
from src.infrastructure.repositories.program_repository import (
    SQLModelProgramRepository,
)


@pytest.mark.asyncio
async def test_create_program_flushes_parent_rows_before_slots() -> None:
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result

    pending: list[object] = []
    flush_snapshots: list[list[type]] = []
    session.add.side_effect = pending.append
    session.add_all.side_effect = pending.extend

    async def record_flush() -> None:
        flush_snapshots.append([type(item) for item in pending])

    session.flush.side_effect = record_flush

    program_id = uuid4()
    program = TrainingProgram(
        id=program_id,
        user_id=uuid4(),
        name="Test Program",
        goal="muscle_gain",
        training_level="beginner",
        duration_weeks=6,
        days_per_week=4,
        session_duration_minutes=60,
        preferred_split=PreferredSplit.UPPER_LOWER,
        status=ProgramStatus.ACTIVE,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 1) + timedelta(weeks=6, days=-1),
    )
    program.templates = ProgramTemplateFactory().create_weekly_structure(
        program_id=program.id,
        goal=program.goal,
        days_per_week=program.days_per_week,
        level=program.training_level,
        preferred_split=program.preferred_split,
        focus_areas=[],
        session_duration_minutes=program.session_duration_minutes,
    )

    await SQLModelProgramRepository(session).create_program(program)

    assert len(flush_snapshots) == 3
    assert flush_snapshots[0] == [TrainingProgramModel]
    assert flush_snapshots[1].count(ProgramWorkoutTemplateModel) == 4
    assert ProgramTemplateSlotModel not in flush_snapshots[1]
    assert flush_snapshots[2].count(ProgramTemplateSlotModel) == 24
