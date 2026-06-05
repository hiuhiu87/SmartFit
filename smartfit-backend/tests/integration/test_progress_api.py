from pathlib import Path
from datetime import date
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from src.domain.common.enums import (
    Goal,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
)
from src.infrastructure.database.base import import_models, metadata, utcnow
from src.infrastructure.database.models.exercise_model import (
    ExerciseAlternativeModel,
    ExerciseModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import (
    UserEquipmentModel,
    UserModel,
    UserPreferenceModel,
    UserProfileModel,
)
from src.infrastructure.database.models.workout_model import (
    WorkoutFeedbackModel,
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.seed.seed_exercises import _seed_rows


@pytest_asyncio.fixture
async def progress_test_context(tmp_path: Path):
    db_path = tmp_path / "progress_test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", future=True, echo=False
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


async def _register_and_login(client: AsyncClient, email: str) -> tuple[str, str]:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return (
        register_response.json()["data"]["id"],
        login_response.json()["data"]["access_token"],
    )


async def _seed_user_basics(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    preferred_days: list[str] | None = None,
) -> None:
    preferred_days = preferred_days or ["monday", "wednesday", "friday", "saturday"]
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="Progress User",
                training_level=TrainingLevel.BEGINNER.value,
                primary_goal=Goal.MUSCLE_GAIN.value,
                injuries=[],
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            UserPreferenceModel(
                user_id=UUID(user_id),
                workout_style="balanced",
                preferred_workout_days=preferred_days,
                preferred_session_minutes=45,
                dislikes=[],
                preference_metadata={},
                created_at=now,
                updated_at=now,
            )
        )
        for equipment in ["dumbbell", "bench", "bodyweight"]:
            session.add(
                UserEquipmentModel(
                    user_id=UUID(user_id),
                    equipment_type=equipment,
                    created_at=now,
                )
            )
        for day, score in [
            ("2026-05-26", 60),
            ("2026-05-28", 70),
            ("2026-05-30", 74),
        ]:
            session.add(
                ReadinessScoreModel(
                    user_id=UUID(user_id),
                    date=date.fromisoformat(day),
                    score=score,
                    category=ReadinessCategory.GOOD.value,
                    recommendation=ReadinessRecommendation.TRAIN_NORMAL.value,
                    confidence=0.9,
                    explanation="seeded",
                    created_at=now,
                    updated_at=now,
                )
            )
        await session.commit()


async def _complete_workout(
    client: AsyncClient,
    token: str,
    workout_date: str,
    focus_muscle: str,
    sets: list[tuple[float, int]],
) -> dict:
    generated = (
        await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "date": workout_date,
                "focus_muscle": focus_muscle,
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "avoid_exercises": [],
            },
        )
    ).json()["data"]
    started = (
        await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": f"{workout_date}T18:00:00Z"},
        )
    ).json()["data"]
    target_exercise = next(
        (
            item
            for item in generated["exercises"]
            if item["primary_muscle"] == focus_muscle
        ),
        generated["exercises"][0],
    )
    for index, (weight, reps) in enumerate(sets, start=1):
        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": started["workout_log_id"],
                "workout_plan_exercise_id": target_exercise["workout_plan_exercise_id"],
                "set_number": index,
                "weight": weight,
                "reps": reps,
                "rpe": 7,
                "completed": True,
            },
        )
        assert response.status_code == 200
    completed = await client.post(
        f"/api/v1/workouts/{generated['workout_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workout_log_id": started["workout_log_id"],
            "completed_at": f"{workout_date}T19:00:00Z",
            "duration_minutes": 50,
            "difficulty_feedback": "just_right",
        },
    )
    assert completed.status_code == 200
    return {
        "generated": generated,
        "started": started,
        "completed": completed.json()["data"],
    }


@pytest.mark.asyncio
async def test_progress_overview_empty_state(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(client, "progress.empty@example.com")
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        response = await client.get(
            "/api/v1/progress/overview?from_date=2026-05-25&to_date=2026-05-31",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["weekly_workouts_completed"] == 0
    assert payload["total_volume_this_week"] == 0
    assert payload["muscle_distribution"] == []


@pytest.mark.asyncio
async def test_progress_overview_with_completed_workouts(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "progress.overview@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        await _complete_workout(
            client, token, "2026-05-26", "chest", [(20, 10), (20, 8)]
        )
        response = await client.get(
            "/api/v1/progress/overview?from_date=2026-05-25&to_date=2026-05-31",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["weekly_workouts_completed"] == 1
    assert payload["total_volume_this_week"] == 360
    assert payload["consistency_percentage"] == 25


@pytest.mark.asyncio
async def test_progress_muscle_distribution(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "progress.muscle@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        await _complete_workout(client, token, "2026-05-26", "chest", [(20, 10)])
        await _complete_workout(client, token, "2026-05-28", "back", [(18, 10)])
        response = await client.get(
            "/api/v1/progress/overview?from_date=2026-05-25&to_date=2026-05-31",
            headers={"Authorization": f"Bearer {token}"},
        )

    items = response.json()["data"]["muscle_distribution"]
    muscles = {item["muscle"] for item in items}
    assert "chest" in muscles
    assert len(muscles) >= 2
    assert abs(sum(item["percentage"] for item in items) - 100) <= 1


@pytest.mark.asyncio
async def test_average_readiness_this_week(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "progress.readiness@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        response = await client.get(
            "/api/v1/progress/overview?from_date=2026-05-25&to_date=2026-05-31",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.json()["data"]["average_readiness_this_week"] == pytest.approx(68.0)


@pytest.mark.asyncio
async def test_personal_records(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(client, "progress.pr@example.com")
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        await _complete_workout(
            client, token, "2026-05-26", "chest", [(20, 10), (22, 8)]
        )
        response = await client.get(
            "/api/v1/progress/personal-records?limit=20",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["best_weight"] == 22
    assert item["best_set_volume"] == 200
    assert item["estimated_1rm"] == pytest.approx(27.87)


@pytest.mark.asyncio
async def test_personal_records_filter_by_exercise(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "progress.pr.filter@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        workout_a = await _complete_workout(
            client, token, "2026-05-26", "chest", [(20, 10)]
        )
        workout_b = await _complete_workout(
            client, token, "2026-05-28", "back", [(18, 10)]
        )
        exercise_id = workout_a["generated"]["exercises"][0]["exercise_id"]
        response = await client.get(
            f"/api/v1/progress/personal-records?limit=20&exercise_id={exercise_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["exercise_id"] == exercise_id


@pytest.mark.asyncio
async def test_weekly_report(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "progress.report@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_id)
        await _complete_workout(client, token, "2026-05-30", "chest", [(20, 10)])
        response = await client.get(
            "/api/v1/progress/weekly-report?week_start=2026-05-25",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]
    assert payload["highlights"]
    assert payload["suggestions"]


@pytest.mark.asyncio
async def test_user_cannot_see_other_user_progress(progress_test_context) -> None:
    app = progress_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_a_id, token_a = await _register_and_login(
            client, "progress.owner.a@example.com"
        )
        user_b_id, token_b = await _register_and_login(
            client, "progress.owner.b@example.com"
        )
        await _seed_user_basics(progress_test_context["session_factory"], user_a_id)
        await _seed_user_basics(progress_test_context["session_factory"], user_b_id)
        await _complete_workout(client, token_a, "2026-05-30", "chest", [(20, 10)])
        response = await client.get(
            "/api/v1/progress/overview?from_date=2026-05-25&to_date=2026-05-31",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["weekly_workouts_completed"] == 0
