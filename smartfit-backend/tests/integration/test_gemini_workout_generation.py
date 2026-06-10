from pathlib import Path
from datetime import date
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.container import container
from app.settings import get_settings
from app.main import create_app
from src.domain.ai.entities import AIWorkoutExerciseResult, AIWorkoutGenerationResult
from src.domain.common.enums import (
    Goal,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
)
from src.domain.common.exceptions import (
    AIConfigurationError,
    AIExerciseMappingError,
    AIInvalidOutputError,
    AIUnsafeOutputError,
)
from src.infrastructure.ai.openrouter_workout_generator import (
    OpenRouterWorkoutGenerator,
)
from src.infrastructure.database.base import import_models, metadata, utcnow
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


class FakeGeminiGenerator:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc

    async def generate_workout(self, context):
        if self.exc is not None:
            raise self.exc
        return self.result


@pytest_asyncio.fixture
async def gemini_test_context(tmp_path: Path):
    db_path = tmp_path / "gemini_workout_test.sqlite3"
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

    original_generator = container.gemini_workout_generator_impl
    yield {
        "app": app,
        "session_factory": session_factory,
        "original_generator": original_generator,
    }
    container.gemini_workout_generator_impl = original_generator
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
    equipment = equipment or ["dumbbell", "bench", "bodyweight"]
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="Gemini User",
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


def _valid_ai_result(slug: str = "dumbbell-bench-press", rpe: int = 7):
    return AIWorkoutGenerationResult(
        workout_title="Chest Dumbbell Day",
        training_decision="normal_volume",
        estimated_duration_minutes=45,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug=slug,
                sets=3,
                reps="8-10",
                rest_seconds=90,
                rpe=rpe,
                notes="Keep shoulder blades stable.",
            ),
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-shoulder-press",
                sets=3,
                reps="8-10",
                rest_seconds=90,
                rpe=rpe,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="push-up",
                sets=3,
                reps="8-12",
                rest_seconds=60,
                rpe=rpe,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-lateral-raise",
                sets=2,
                reps="12-15",
                rest_seconds=45,
                rpe=rpe,
            ),
        ],
        reasoning_summary="Generated by Gemini.",
        safety_note="Stop if you feel sharp pain, dizziness, or unusual discomfort.",
    )


def _continuous_cardio_ai_result():
    return AIWorkoutGenerationResult(
        workout_title="Recovery Walk Session",
        training_decision="recovery",
        estimated_duration_minutes=20,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug="push-up",
                sets=2,
                reps="8-10",
                rest_seconds=60,
                rpe=4,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="plank",
                sets=2,
                reps="30 seconds",
                rest_seconds=30,
                rpe=4,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="treadmill-zone-2-walk",
                sets=1,
                reps="20 minutes",
                rest_seconds=0,
                rpe=4,
                notes="Maintain a conversational pace.",
            ),
        ],
        reasoning_summary="Continuous cardio block with no rest interval.",
        safety_note="Stop if you feel sharp pain, dizziness, or unusual discomfort.",
    )


def _missing_movement_mix_ai_result() -> AIWorkoutGenerationResult:
    return AIWorkoutGenerationResult(
        workout_title="Incomplete Push Day",
        training_decision="normal_volume",
        estimated_duration_minutes=45,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-bench-press",
                sets=3,
                reps="8-10",
                rest_seconds=90,
                rpe=7,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-incline-press",
                sets=3,
                reps="8-10",
                rest_seconds=90,
                rpe=7,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="push-up",
                sets=3,
                reps="8-12",
                rest_seconds=60,
                rpe=7,
            ),
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-lateral-raise",
                sets=2,
                reps="12-15",
                rest_seconds=45,
                rpe=7,
            ),
        ],
        reasoning_summary="Missing the required vertical push pattern.",
        safety_note="Stop if you feel sharp pain.",
    )


@pytest.mark.asyncio
async def test_generate_workout_rule_based_mode_still_works(
    gemini_test_context,
) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_valid_ai_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.rulebased@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "rule_based",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_generate_workout_gemini_mode_success_with_fake_client(
    gemini_test_context,
) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_valid_ai_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.success@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "gemini",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["source"] == "ai"
    assert payload["status"] == "generated"
    assert payload["exercises"][0]["name"] == "Dumbbell Bench Press"


@pytest.mark.asyncio
async def test_ai_missing_required_movement_pattern_falls_back_in_auto_mode(
    gemini_test_context,
) -> None:
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_missing_movement_mix_ai_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=gemini_test_context["app"]),
        base_url="http://testserver",
    ) as client:
        user_id, token = await _register_and_login(
            client, "gemini.missing-pattern@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "full_body",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "auto",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_generate_workout_auto_fallback_when_gemini_invalid_json(
    gemini_test_context,
) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        exc=AIInvalidOutputError("invalid json")
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.autofallback@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "auto",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_generate_workout_gemini_mode_invalid_json_returns_error(
    gemini_test_context,
) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        exc=AIInvalidOutputError("invalid json")
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.invalidjson@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "gemini",
            },
        )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ai_generation_error"


@pytest.mark.asyncio
async def test_gemini_cannot_use_unknown_exercise_slug(gemini_test_context) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_valid_ai_result(slug="unknown_slug")
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.unknownslug@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        gemini_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "gemini",
            },
        )
        auto_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "auto",
            },
        )

    assert gemini_response.status_code == 502
    assert auto_response.status_code == 200
    assert auto_response.json()["data"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_gemini_low_readiness_safety_guardrail(gemini_test_context) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_valid_ai_result(rpe=9)
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.lowreadiness@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 30
        )
        gemini_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "gemini",
            },
        )
        auto_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "auto",
            },
        )

    assert gemini_response.status_code == 502
    assert auto_response.status_code == 200
    assert auto_response.json()["data"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_generation_mode_validation(gemini_test_context) -> None:
    app = gemini_test_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.invalidmode@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "invalid",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_openrouter_api_key(gemini_test_context, monkeypatch) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = OpenRouterWorkoutGenerator(
        container.get_gemini_prompt_builder(),
        container.get_ai_workout_schema_validator(),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    get_settings.cache_clear()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.nokey@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"], user_id, 78
        )
        auto_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "auto",
            },
        )
        openrouter_response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "focus_muscle": "chest",
                "available_time_minutes": 45,
                "equipment": ["dumbbell", "bench", "bodyweight"],
                "generation_mode": "openrouter",
            },
        )
    get_settings.cache_clear()

    assert auto_response.status_code == 200
    assert auto_response.json()["data"]["source"] == "fallback"
    assert openrouter_response.status_code == 503
    assert openrouter_response.json()["error"]["code"] == "ai_configuration_error"


@pytest.mark.asyncio
async def test_gemini_allows_zero_rest_for_continuous_cardio(
    gemini_test_context,
) -> None:
    app = gemini_test_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiGenerator(
        result=_continuous_cardio_ai_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, access_token = await _register_and_login(
            client, "gemini.cardiozero@example.com"
        )
        await _seed_profile_equipment_and_readiness(
            gemini_test_context["session_factory"],
            user_id,
            52,
            equipment=["treadmill", "bodyweight"],
        )
        response = await client.post(
            "/api/v1/workouts/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "available_time_minutes": 30,
                "equipment": ["treadmill", "bodyweight"],
                "generation_mode": "gemini",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["source"] == "ai"
    cardio = next(
        item for item in payload["exercises"] if item["name"] == "Treadmill Zone 2 Walk"
    )
    assert cardio["rest_seconds"] == 0
