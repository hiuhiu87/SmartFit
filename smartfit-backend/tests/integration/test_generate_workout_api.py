from pathlib import Path
from datetime import date
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
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.models.ai_model import (
    AIRequestModel,
    AIUsageDailyModel,
)
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
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.seed.seed_exercises import _seed_rows


@pytest_asyncio.fixture
async def workout_test_context(tmp_path: Path):
    db_path = tmp_path / "generate_workout_test.sqlite3"
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
                    AIRequestModel.__table__,
                    AIUsageDailyModel.__table__,
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
    user_id = register_response.json()["data"]["id"]
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    access_token = login_response.json()["data"]["access_token"]
    return user_id, access_token


async def _seed_profile_equipment_and_readiness(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    readiness_score: float,
    target_date: str = "2026-05-31",
    equipment: list[str] | None = None,
) -> None:
    target_date_value = date.fromisoformat(target_date)
    equipment = equipment or ["dumbbell"]
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="Workout User",
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
                explanation="seeded",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_generate_chest_dumbbell_workout_success(workout_test_context) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.chest@example.com"
        )
        await _seed_profile_equipment_and_readiness(session_factory, user_id, 78)
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 60,
                "equipment": ["dumbbell", "bench"],
                "generation_mode": "rule_based",
                "avoid_exercises": [],
                "user_note": "I feel okay today.",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["source"] == "fallback"
    assert payload["status"] == "generated"
    assert payload["focus_muscle"] == "chest"
    assert payload["estimated_duration_minutes"] == 60
    assert len(payload["exercises"]) >= 5
    assert payload["exercises"]
    assert all(
        item["equipment"] in {"dumbbell", "bodyweight"} for item in payload["exercises"]
    )

    async with session_factory() as session:
        saved = await session.get(WorkoutPlanModel, UUID(payload["workout_id"]))
        assert saved is not None


@pytest.mark.asyncio
async def test_generate_upper_pull_rule_based_structured_workout(
    workout_test_context,
) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.upperpull@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            session_factory,
            user_id,
            72,
            equipment=["barbell", "dumbbell", "bench", "bodyweight", "bike"],
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "upper_body_pull",
                "available_time_minutes": 60,
                "equipment": ["barbell", "dumbbell", "bench", "bodyweight", "bike"],
                "generation_mode": "rule_based",
                "avoid_exercises": [],
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["source"] == "fallback"
    assert payload["status"] == "generated"
    assert payload["focus_muscle"] == "upper_body_pull"
    assert payload["estimated_duration_minutes"] == 60
    assert len(payload["exercises"]) >= 6
    assert len({item["exercise_id"] for item in payload["exercises"]}) == len(
        payload["exercises"]
    )
    assert all(
        item["equipment"] in {"barbell", "dumbbell", "bodyweight", "bike"}
        for item in payload["exercises"]
    )

    async with session_factory() as session:
        saved = await session.get(WorkoutPlanModel, UUID(payload["workout_id"]))
        assert saved is not None
        saved_exercises = await session.execute(
            select(WorkoutPlanExerciseModel).where(
                WorkoutPlanExerciseModel.workout_plan_id == saved.id
            )
        )
        assert len(saved_exercises.scalars().all()) >= 5


@pytest.mark.asyncio
async def test_generate_low_readiness_recovery_workout(workout_test_context) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.lowreadiness@example.com"
        )
        await _seed_profile_equipment_and_readiness(session_factory, user_id, 30)
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell"],
                "generation_mode": "rule_based",
                "avoid_exercises": [],
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["training_decision"] in {"recovery", "reduced_volume"}
    assert all(item["target_rpe"] <= 7 for item in payload["exercises"])


@pytest.mark.asyncio
async def test_generate_workout_missing_readiness_fails(workout_test_context) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.noreadiness@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            session_factory, user_id, 78, target_date="2026-05-30"
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell"],
                "generation_mode": "rule_based",
                "avoid_exercises": [],
            },
        )

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_generate_workout_uses_user_default_equipment_when_request_equipment_empty(
    workout_test_context,
) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.defaultequipment@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            session_factory, user_id, 75, equipment=["dumbbell"]
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": [],
                "generation_mode": "rule_based",
                "avoid_exercises": [],
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["exercises"]
    assert all(
        item["equipment"] in {"dumbbell", "bodyweight"} for item in payload["exercises"]
    )


@pytest.mark.asyncio
async def test_generate_workout_avoids_exercises(workout_test_context) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.avoid@example.com"
        )
        await _seed_profile_equipment_and_readiness(session_factory, user_id, 78)
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 60,
                "equipment": ["dumbbell", "bench"],
                "generation_mode": "rule_based",
                "avoid_exercises": ["Dumbbell Bench Press"],
            },
        )

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["data"]["exercises"]}
    assert "Dumbbell Bench Press" not in names


@pytest.mark.asyncio
async def test_generate_workout_accepts_legacy_payload_keys(
    workout_test_context,
) -> None:
    app = workout_test_context["app"]
    session_factory = workout_test_context["session_factory"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "generate.legacykeys@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            session_factory,
            user_id,
            72,
            target_date=str(date.today()),
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "focus": "full_body",
                "available_minutes": 45,
                "equipment_types": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "rule_based",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "generated"
    assert payload["source"] == "fallback"
    assert payload["exercises"]
