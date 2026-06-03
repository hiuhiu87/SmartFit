from pathlib import Path
from datetime import date
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.models.exercise_model import (
    ExerciseAlternativeModel,
    ExerciseModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import (
    UserEquipmentModel,
    UserModel,
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
from src.domain.common.enums import (
    Goal,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
)


@pytest_asyncio.fixture
async def workout_lifecycle_context(tmp_path: Path):
    db_path = tmp_path / "workout_lifecycle_test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", future=True, echo=False
    )
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: UserModel.metadata.create_all(
                sync_conn,
                tables=[
                    UserModel.__table__,
                    UserProfileModel.__table__,
                    UserEquipmentModel.__table__,
                    ReadinessScoreModel.__table__,
                    ExerciseModel.__table__,
                    ExerciseAlternativeModel.__table__,
                    WorkoutPlanModel.__table__,
                    WorkoutPlanExerciseModel.__table__,
                    WorkoutLogModel.__table__,
                    WorkoutSetLogModel.__table__,
                    WorkoutFeedbackModel.__table__,
                ],
            )
        )

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
    user_id = register_response.json()["data"]["id"]
    access_token = login_response.json()["data"]["access_token"]
    return user_id, access_token


async def _seed_profile_and_readiness(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    readiness_score: float = 78,
    target_date: str = "2026-05-31",
    equipment: list[str] | None = None,
) -> None:
    equipment = equipment or ["dumbbell", "bench", "bodyweight"]
    target_date_value = date.fromisoformat(target_date)
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="Lifecycle User",
                training_level=TrainingLevel.BEGINNER.value,
                primary_goal=Goal.MUSCLE_GAIN.value,
                injuries=[],
                created_at=now,
                updated_at=now,
            )
        )
        for equipment_type in equipment:
            session.add(
                UserEquipmentModel(
                    user_id=UUID(user_id),
                    equipment_type=equipment_type,
                    created_at=now,
                )
            )
        session.add(
            ReadinessScoreModel(
                user_id=UUID(user_id),
                date=target_date_value,
                score=readiness_score,
                category=ReadinessCategory.GOOD.value,
                recommendation=ReadinessRecommendation.TRAIN_NORMAL.value,
                confidence=0.9,
                explanation="seeded readiness",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _generate_workout(client: AsyncClient, token: str) -> dict:
    response = await client.post(
        "/api/v1/workouts/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": "2026-05-31",
            "focus_muscle": "chest",
            "available_time_minutes": 45,
            "equipment": ["dumbbell", "bench", "bodyweight"],
            "avoid_exercises": [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_get_workout_detail_success(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    session_factory = workout_lifecycle_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.detail@example.com"
        )
        await _seed_profile_and_readiness(session_factory, user_id)
        generated = await _generate_workout(client, token)
        response = await client.get(
            f"/api/v1/workouts/{generated['workout_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["workout_id"] == generated["workout_id"]
    assert payload["exercises"]


@pytest.mark.asyncio
async def test_start_workout_success(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.start@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:00:00Z"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "started"
    assert payload["workout_log_id"]


@pytest.mark.asyncio
async def test_start_workout_idempotent(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.start.idempotent@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        first = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:00:00Z"},
        )
        second = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:05:00Z"},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert (
        first.json()["data"]["workout_log_id"]
        == second.json()["data"]["workout_log_id"]
    )


@pytest.mark.asyncio
async def test_log_set_success(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.logset@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        started = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:00:00Z"},
        )
        workout_log_id = started.json()["data"]["workout_log_id"]
        exercise_id = generated["exercises"][0]["workout_plan_exercise_id"]
        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "workout_plan_exercise_id": exercise_id,
                "set_number": 1,
                "weight": 20,
                "reps": 10,
                "rpe": 7,
                "completed": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["set_log_id"]


@pytest.mark.asyncio
async def test_log_set_upsert_same_set_number(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    session_factory = workout_lifecycle_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.upsertset@example.com"
        )
        await _seed_profile_and_readiness(session_factory, user_id)
        generated = await _generate_workout(client, token)
        started = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:00:00Z"},
        )
        workout_log_id = started.json()["data"]["workout_log_id"]
        exercise_id = generated["exercises"][0]["workout_plan_exercise_id"]
        await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "workout_plan_exercise_id": exercise_id,
                "set_number": 1,
                "weight": 20,
                "reps": 10,
                "rpe": 7,
                "completed": True,
            },
        )
        await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "workout_plan_exercise_id": exercise_id,
                "set_number": 1,
                "weight": 20,
                "reps": 12,
                "rpe": 8,
                "completed": True,
            },
        )

    async with session_factory() as session:
        total = (
            await session.execute(select(func.count()).select_from(WorkoutSetLogModel))
        ).scalar_one()
        saved = (await session.execute(select(WorkoutSetLogModel))).scalars().one()

    assert total == 1
    assert saved.reps_completed == 12
    assert saved.rpe == 8


@pytest.mark.asyncio
async def test_cannot_log_set_before_start(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.beforestart@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": generated["workout_id"],
                "workout_plan_exercise_id": generated["exercises"][0][
                    "workout_plan_exercise_id"
                ],
                "set_number": 1,
                "weight": 20,
                "reps": 10,
                "rpe": 7,
                "completed": True,
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_complete_workout_success_and_volume_calculated(
    workout_lifecycle_context,
) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.complete@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        started = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={"started_at": "2026-05-31T18:00:00Z"},
        )
        workout_log_id = started.json()["data"]["workout_log_id"]
        exercise_id = generated["exercises"][0]["workout_plan_exercise_id"]

        for set_number, weight, reps in [(1, 20, 10), (2, 20, 8), (3, 18, 10)]:
            response = await client.post(
                f"/api/v1/workouts/{generated['workout_id']}/sets",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "workout_log_id": workout_log_id,
                    "workout_plan_exercise_id": exercise_id,
                    "set_number": set_number,
                    "weight": weight,
                    "reps": reps,
                    "rpe": 7,
                    "completed": True,
                },
            )
            assert response.status_code == 200

        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "completed_at": "2026-05-31T19:00:00Z",
                "duration_minutes": 58,
                "calories_burned": 310,
                "avg_heart_rate": 128,
                "difficulty_feedback": "just_right",
                "energy_after": 7,
                "notes": "Good session.",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "completed"
    assert payload["total_volume"] == 540


@pytest.mark.asyncio
async def test_cannot_complete_generated_workout_before_start(
    workout_lifecycle_context,
) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.complete.beforestart@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": generated["workout_id"],
                "completed_at": "2026-05-31T19:00:00Z",
                "duration_minutes": 58,
            },
        )

    assert response.status_code == 404 or response.status_code == 400


@pytest.mark.asyncio
async def test_get_workout_history_returns_completed_workout(
    workout_lifecycle_context,
) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "lifecycle.history@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_id
        )
        generated = await _generate_workout(client, token)
        started = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        workout_log_id = started.json()["data"]["workout_log_id"]
        exercise_id = generated["exercises"][0]["workout_plan_exercise_id"]
        await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/sets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "workout_plan_exercise_id": exercise_id,
                "set_number": 1,
                "weight": 20,
                "reps": 10,
                "rpe": 7,
                "completed": True,
            },
        )
        await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_log_id": workout_log_id,
                "duration_minutes": 40,
                "difficulty_feedback": "just_right",
            },
        )
        response = await client.get(
            "/api/v1/workouts/history",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"]
    assert payload["items"][0]["workout_id"] == generated["workout_id"]


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_workout(workout_lifecycle_context) -> None:
    app = workout_lifecycle_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_a_id, token_a = await _register_and_login(
            client, "lifecycle.owner.a@example.com"
        )
        user_b_id, token_b = await _register_and_login(
            client, "lifecycle.owner.b@example.com"
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_a_id
        )
        await _seed_profile_and_readiness(
            workout_lifecycle_context["session_factory"], user_b_id
        )
        generated = await _generate_workout(client, token_a)

        get_response = await client.get(
            f"/api/v1/workouts/{generated['workout_id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        start_response = await client.post(
            f"/api/v1/workouts/{generated['workout_id']}/start",
            headers={"Authorization": f"Bearer {token_b}"},
            json={},
        )

    assert get_response.status_code == 404
    assert start_response.status_code == 404
