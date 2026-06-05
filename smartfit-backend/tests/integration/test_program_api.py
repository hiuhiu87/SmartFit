from datetime import date
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import select

from app.main import create_app
from src.domain.common.enums import (
    Goal,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
)
from src.domain.exercise.equipment_policy import get_equipment_category
from src.infrastructure.database.base import import_models, metadata, utcnow
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.program_model import (
    ProgramWorkoutInstanceModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import (
    UserEquipmentModel,
    UserProfileModel,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.seed.seed_exercises import _seed_rows


@pytest_asyncio.fixture
async def program_test_context(tmp_path: Path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'program_test.sqlite3'}",
        future=True,
        echo=False,
    )
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with engine.begin() as connection:
        import_models()
        await connection.run_sync(metadata.create_all)
    async with session_factory() as session:
        session.add_all(_seed_rows())
        await session.commit()

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    yield {"app": app, "session_factory": session_factory}
    app.dependency_overrides.clear()
    await engine.dispose()


async def _register_user(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    email: str,
) -> tuple[str, str]:
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    user_id = registered.json()["data"]["id"]
    logged_in = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = logged_in.json()["data"]["access_token"]
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="Program User",
                training_level=TrainingLevel.BEGINNER.value,
                primary_goal=Goal.MUSCLE_GAIN.value,
                injuries=[],
                created_at=now,
                updated_at=now,
            )
        )
        for equipment in (
            "barbell",
            "dumbbell",
            "bench",
            "cable_machine",
            "machine",
            "bodyweight",
            "treadmill",
            "bike",
        ):
            session.add(
                UserEquipmentModel(
                    user_id=UUID(user_id),
                    equipment_type=equipment,
                    created_at=now,
                )
            )
        await session.commit()
    return user_id, token


async def _seed_readiness(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    target_date: date,
    score: float,
) -> None:
    recommendation = (
        ReadinessRecommendation.RECOVERY
        if score < 45
        else ReadinessRecommendation.TRAIN_NORMAL
    )
    category = ReadinessCategory.LOW if score < 45 else ReadinessCategory.GOOD
    now = utcnow()
    async with session_factory() as session:
        session.add(
            ReadinessScoreModel(
                user_id=UUID(user_id),
                date=target_date,
                score=score,
                category=category.value,
                recommendation=recommendation.value,
                confidence=0.9,
                explanation="seeded",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _create_program(
    client: AsyncClient,
    token: str,
    start_date: str = "2026-06-01",
) -> dict:
    response = await client.post(
        "/api/v1/programs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "goal": "muscle_gain",
            "duration_weeks": 6,
            "days_per_week": 4,
            "session_duration_minutes": 60,
            "preferred_split": "upper_lower",
            "focus_areas": ["posture", "back"],
            "generation_mode": "rule_based",
            "start_date": start_date,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_program_4_days_upper_lower(program_test_context) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        _, token = await _register_user(
            client,
            program_test_context["session_factory"],
            "program.create@example.com",
        )
        program = await _create_program(client, token)

    assert [item["title"] for item in program["weekly_structure"]] == [
        "Upper Push Balanced",
        "Lower Body + Core",
        "Upper Pull Posture",
        "Full Body Conditioning",
    ]
    assert program["training_style"] == "balanced"
    assert all(len(item["slots"]) == 6 for item in program["weekly_structure"])


@pytest.mark.asyncio
async def test_get_active_program(program_test_context) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        _, token = await _register_user(
            client,
            program_test_context["session_factory"],
            "program.active@example.com",
        )
        created = await _create_program(client, token)
        response = await client.get(
            "/api/v1/programs/active",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]
    assert response.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_today_program_workout(program_test_context) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        _, token = await _register_user(
            client,
            program_test_context["session_factory"],
            "program.today@example.com",
        )
        await _create_program(client, token)
        response = await client.get(
            "/api/v1/programs/active/today?date=2026-06-04",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()["data"]
    assert response.status_code == 200
    assert payload["week_number"] == 1
    assert payload["day_index"] == 2
    assert payload["template"]["title"] == "Upper Pull Posture"
    assert payload["status"] == "scheduled"


@pytest.mark.asyncio
async def test_generate_today_workout_from_program(program_test_context) -> None:
    session_factory = program_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        user_id, token = await _register_user(
            client, session_factory, "program.generate@example.com"
        )
        await _create_program(client, token)
        await _seed_readiness(
            session_factory, user_id, date.fromisoformat("2026-06-01"), 78
        )
        response = await client.post(
            "/api/v1/programs/active/today/generate?date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert len(payload["exercises"]) >= 5
    async with session_factory() as session:
        result = await session.execute(
            select(ProgramWorkoutInstanceModel).where(
                ProgramWorkoutInstanceModel.actual_workout_plan_id
                == UUID(payload["workout_id"])
            )
        )
        instance = result.scalar_one_or_none()
        assert instance is not None
        assert instance.status == "generated"


@pytest.mark.asyncio
async def test_generate_all_four_program_days_with_diverse_equipment(
    program_test_context,
) -> None:
    session_factory = program_test_context["session_factory"]
    dates = [
        date.fromisoformat("2026-06-01"),
        date.fromisoformat("2026-06-02"),
        date.fromisoformat("2026-06-04"),
        date.fromisoformat("2026-06-05"),
    ]
    generated = []
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        user_id, token = await _register_user(
            client, session_factory, "program.four-days@example.com"
        )
        await _create_program(client, token)
        for target_date in dates:
            await _seed_readiness(session_factory, user_id, target_date, 78)
            response = await client.post(
                f"/api/v1/programs/active/today/generate?date={target_date.isoformat()}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200, response.text
            generated.append(response.json()["data"])

    cardio_days = 0
    async with session_factory() as session:
        for payload in generated:
            assert 5 <= len(payload["exercises"]) <= 6
            exercise_ids = [UUID(item["exercise_id"]) for item in payload["exercises"]]
            result = await session.execute(
                select(ExerciseModel).where(ExerciseModel.id.in_(exercise_ids))
            )
            exercises = result.scalars().all()
            patterns = {
                item.movement_pattern or item.movement_type for item in exercises
            }
            categories = {
                get_equipment_category(item.equipment_type) for item in exercises
            }
            assert len(patterns) >= 3
            assert len(categories) >= 2
            if "cardio" in patterns:
                cardio_days += 1
    assert cardio_days >= 1


@pytest.mark.asyncio
async def test_low_readiness_program_workout_reduced(program_test_context) -> None:
    session_factory = program_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        user_id, token = await _register_user(
            client, session_factory, "program.low@example.com"
        )
        await _create_program(client, token)
        await _seed_readiness(
            session_factory, user_id, date.fromisoformat("2026-06-01"), 30
        )
        response = await client.post(
            "/api/v1/programs/active/today/generate?date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()["data"]
    assert response.status_code == 200
    assert payload["training_decision"] in {"recovery", "reduced_volume"}
    assert all(item["target_rpe"] <= 7 for item in payload["exercises"])


@pytest.mark.asyncio
async def test_skip_program_workout(program_test_context) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        _, token = await _register_user(
            client,
            program_test_context["session_factory"],
            "program.skip@example.com",
        )
        await _create_program(client, token)
        today = await client.get(
            "/api/v1/programs/active/today?date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.post(
            f"/api/v1/programs/workouts/{today.json()['data']['instance_id']}/skip",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "skipped"


@pytest.mark.asyncio
async def test_reschedule_program_workout(program_test_context) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        _, token = await _register_user(
            client,
            program_test_context["session_factory"],
            "program.reschedule@example.com",
        )
        await _create_program(client, token)
        today = await client.get(
            "/api/v1/programs/active/today?date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        instance_id = today.json()["data"]["instance_id"]
        response = await client.post(
            f"/api/v1/programs/workouts/{instance_id}/reschedule",
            headers={"Authorization": f"Bearer {token}"},
            json={"scheduled_date": "2026-06-03"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rescheduled"
    async with AsyncClient(
        transport=ASGITransport(app=program_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        original_date = await client.get(
            "/api/v1/programs/active/today?date=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        new_date = await client.get(
            "/api/v1/programs/active/today?date=2026-06-03",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert original_date.json()["data"]["scheduled"] is False
    assert new_date.json()["data"]["instance_id"] == instance_id
    assert new_date.json()["data"]["status"] == "rescheduled"
    async with program_test_context["session_factory"]() as session:
        instance = await session.get(ProgramWorkoutInstanceModel, UUID(instance_id))
        assert instance.scheduled_date == date.fromisoformat("2026-06-03")
