from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.container import container
from app.main import create_app
from src.domain.ai.entities import (
    AIChatResult,
    AIChatSuggestedAction,
    AIWorkoutExerciseResult,
    AIWorkoutGenerationResult,
)
from src.domain.common.enums import (
    Goal,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
)
from src.domain.common.exceptions import AIInvalidOutputError, AIProviderTimeoutError
from src.infrastructure.database.base import import_models, metadata, utcnow
from src.infrastructure.database.models.ai_model import (
    AIChatMessageModel,
    AIRequestModel,
    AIUsageDailyModel,
)
from src.infrastructure.database.models.exercise_model import (
    ExerciseAlternativeModel,
    ExerciseModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.subscription_model import SubscriptionModel
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


class FakeGeminiWorkoutGenerator:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc
        self.called = 0

    async def generate_workout(self, context):
        self.called += 1
        if self.exc is not None:
            raise self.exc
        return self.result


class FakeGeminiChatGenerator:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc
        self.called = 0

    async def chat(self, context):
        self.called += 1
        if self.exc is not None:
            raise self.exc
        return self.result

    async def generate_workout(self, context):
        raise NotImplementedError


@pytest_asyncio.fixture
async def ai_usage_context(tmp_path: Path):
    db_path = tmp_path / "ai_usage_test.sqlite3"
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

    original_workout_generator = container.gemini_workout_generator_impl
    original_chat_generator = container.gemini_ai_chat_generator_impl
    yield {
        "app": app,
        "session_factory": session_factory,
        "original_workout_generator": original_workout_generator,
        "original_chat_generator": original_chat_generator,
    }
    container.gemini_workout_generator_impl = original_workout_generator
    container.gemini_ai_chat_generator_impl = original_chat_generator
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


async def _seed_profile_and_readiness(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    readiness_score: float = 72,
    target_date: str = "2026-06-01",
) -> None:
    now = utcnow()
    async with session_factory() as session:
        session.add(
            UserProfileModel(
                user_id=UUID(user_id),
                full_name="AI Usage User",
                training_level=TrainingLevel.BEGINNER.value,
                primary_goal=Goal.MUSCLE_GAIN.value,
                injuries=[],
                created_at=now,
                updated_at=now,
            )
        )
        for equipment_type in ["dumbbell", "bench", "bodyweight"]:
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
                date=date.fromisoformat(target_date),
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


def _valid_ai_workout_result() -> AIWorkoutGenerationResult:
    return AIWorkoutGenerationResult(
        workout_title="Chest Dumbbell Day",
        training_decision="normal_volume",
        estimated_duration_minutes=45,
        exercises=[
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-bench-press",
                sets=3,
                reps="8-10",
                rest_seconds=90,
                rpe=7,
                notes="Keep shoulder blades stable.",
            ),
            AIWorkoutExerciseResult(
                exercise_slug="dumbbell-shoulder-press",
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
        reasoning_summary="Generated by Gemini.",
        safety_note="Stop if you feel sharp pain, dizziness, or unusual discomfort.",
    )


async def _get_exercise_id_by_slug(
    session_factory: async_sessionmaker[AsyncSession], slug: str
) -> UUID:
    async with session_factory() as session:
        result = await session.execute(
            select(ExerciseModel).where(ExerciseModel.slug == slug)
        )
        model = result.scalar_one()
        return model.id


def _valid_ai_chat_result(exercise_id: UUID) -> AIChatResult:
    return AIChatResult(
        reply="You can switch to Push-Up and keep 3 sets of 10-12 reps.",
        intent="replace_exercise",
        suggested_action=AIChatSuggestedAction(
            type="replace_exercise",
            exercise_id=exercise_id,
            exercise_name="Push-Up",
            target_sets=3,
            target_reps="10-12",
            rest_seconds=75,
            target_rpe=7,
            reason="Bodyweight fallback for the same muscle group.",
        ),
    )


async def _generate_workout(
    client: AsyncClient, token: str, generation_mode: str
) -> dict:
    response = await client.post(
        "/api/v1/workouts/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": "2026-06-01",
            "focus_muscle": "chest",
            "available_time_minutes": 45,
            "equipment": ["dumbbell", "bench", "bodyweight"],
            "generation_mode": generation_mode,
        },
    )
    return {"status_code": response.status_code, "payload": response.json()}


async def _generate_and_start_workout(client: AsyncClient, token: str) -> dict:
    generated = await client.post(
        "/api/v1/workouts/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date": "2026-06-01",
            "focus_muscle": "chest",
            "available_time_minutes": 45,
            "equipment": ["dumbbell", "bench", "bodyweight"],
            "generation_mode": "rule_based",
        },
    )
    workout = generated.json()["data"]
    started = await client.post(
        f"/api/v1/workouts/{workout['workout_id']}/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"started_at": "2026-06-01T18:00:00Z"},
    )
    workout["workout_log_id"] = started.json()["data"]["workout_log_id"]
    return workout


async def _get_usage_counts(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
) -> AIUsageDailyModel | None:
    target_date = datetime.now(timezone.utc).date()
    async with session_factory() as session:
        result = await session.execute(
            select(AIUsageDailyModel).where(
                AIUsageDailyModel.user_id == UUID(user_id),
                AIUsageDailyModel.date == target_date,
            )
        )
        return result.scalar_one_or_none()


async def _get_ai_requests(
    session_factory: async_sessionmaker[AsyncSession], user_id: str
) -> list[AIRequestModel]:
    async with session_factory() as session:
        result = await session.execute(
            select(AIRequestModel)
            .where(AIRequestModel.user_id == UUID(user_id))
            .order_by(AIRequestModel.created_at.asc(), AIRequestModel.id.asc())
        )
        return list(result.scalars().all())


async def _prefill_usage(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    *,
    ai_workout_count: int = 0,
    ai_chat_count: int = 0,
    ai_replacement_count: int = 0,
    ai_weekly_report_count: int = 0,
    total_ai_count: int = 0,
) -> None:
    now = utcnow()
    async with session_factory() as session:
        session.add(
            AIUsageDailyModel(
                user_id=UUID(user_id),
                date=datetime.now(timezone.utc).date(),
                ai_workout_count=ai_workout_count,
                ai_chat_count=ai_chat_count,
                ai_replacement_count=ai_replacement_count,
                ai_weekly_report_count=ai_weekly_report_count,
                total_ai_count=total_ai_count,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_ai_usage_today_empty(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        _, token = await _register_and_login(client, "ai.usage.empty@example.com")
        response = await client.get(
            "/api/v1/ai/usage/today",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["plan"] == "free"
    assert payload["usage"] == {
        "ai_workout_count": 0,
        "ai_chat_count": 0,
        "ai_replacement_count": 0,
        "ai_weekly_report_count": 0,
        "total_ai_count": 0,
    }
    assert payload["limits"] == {
        "ai_workout_limit": 3,
        "ai_chat_limit": 20,
        "ai_replacement_limit": 10,
        "ai_weekly_report_limit": 3,
        "total_ai_limit": 30,
    }


@pytest.mark.asyncio
async def test_ai_usage_today_uses_premium_subscription(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.premium@example.com"
        )
        async with ai_usage_context["session_factory"]() as session:
            session.add(
                SubscriptionModel(
                    user_id=UUID(user_id),
                    plan="premium",
                    status="active",
                )
            )
            await session.commit()
        response = await client.get(
            "/api/v1/ai/usage/today",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["plan"] == "premium"
    assert payload["limits"] == {
        "ai_workout_limit": 30,
        "ai_chat_limit": 200,
        "ai_replacement_limit": 100,
        "ai_weekly_report_limit": 30,
        "total_ai_limit": 300,
    }


@pytest.mark.asyncio
async def test_ai_workout_generation_increments_usage(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiWorkoutGenerator(
        result=_valid_ai_workout_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.workout@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        response = await _generate_workout(client, token, "gemini")

    usage = await _get_usage_counts(ai_usage_context["session_factory"], user_id)
    assert response["status_code"] == 200
    assert usage is not None
    assert usage.ai_workout_count == 1
    assert usage.total_ai_count == 1


@pytest.mark.asyncio
async def test_rule_based_generation_does_not_increment_ai_usage(
    ai_usage_context,
) -> None:
    app = ai_usage_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiWorkoutGenerator(
        result=_valid_ai_workout_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.rulebased@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        response = await _generate_workout(client, token, "rule_based")

    usage = await _get_usage_counts(ai_usage_context["session_factory"], user_id)
    assert response["status_code"] == 200
    assert response["payload"]["data"]["source"] == "fallback"
    assert usage is None


@pytest.mark.asyncio
async def test_ai_chat_increments_usage(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    workout_generator = FakeGeminiWorkoutGenerator(result=_valid_ai_workout_result())
    replacement_id = await _get_exercise_id_by_slug(
        ai_usage_context["session_factory"], "push-up"
    )
    chat_generator = FakeGeminiChatGenerator(
        result=_valid_ai_chat_result(replacement_id)
    )
    container.gemini_workout_generator_impl = workout_generator
    container.gemini_ai_chat_generator_impl = chat_generator
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(client, "ai.usage.chat@example.com")
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0][
                    "workout_plan_exercise_id"
                ],
                "message": "The machine is busy. What can I do instead?",
            },
        )

    usage = await _get_usage_counts(ai_usage_context["session_factory"], user_id)
    assert response.status_code == 200
    assert usage is not None
    assert usage.ai_chat_count == 1
    assert usage.total_ai_count == 1


@pytest.mark.asyncio
async def test_ai_chat_limit_exceeded_returns_429(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    replacement_id = await _get_exercise_id_by_slug(
        ai_usage_context["session_factory"], "push-up"
    )
    container.gemini_ai_chat_generator_impl = FakeGeminiChatGenerator(
        result=_valid_ai_chat_result(replacement_id)
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.chatlimit@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        await _prefill_usage(
            ai_usage_context["session_factory"],
            user_id,
            ai_chat_count=20,
            total_ai_count=20,
        )
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0][
                    "workout_plan_exercise_id"
                ],
                "message": "The machine is busy. What can I do instead?",
            },
        )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "AI_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_auto_mode_fallback_due_to_provider_error_still_records_ai_request(
    ai_usage_context,
) -> None:
    app = ai_usage_context["app"]
    generator = FakeGeminiWorkoutGenerator(exc=AIInvalidOutputError("invalid json"))
    container.gemini_workout_generator_impl = generator
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.fallback@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        response = await _generate_workout(client, token, "auto")

    usage = await _get_usage_counts(ai_usage_context["session_factory"], user_id)
    requests = await _get_ai_requests(ai_usage_context["session_factory"], user_id)
    assert response["status_code"] == 200
    assert response["payload"]["data"]["source"] == "fallback"
    assert generator.called == 1
    assert usage is not None
    assert usage.ai_workout_count == 1
    assert usage.total_ai_count == 1
    assert len(requests) == 1
    assert requests[0].status == "fallback_used"
    assert requests[0].fallback_used is True


@pytest.mark.asyncio
async def test_auto_mode_fallback_due_to_internal_limit_does_not_call_gemini(
    ai_usage_context,
) -> None:
    app = ai_usage_context["app"]
    generator = FakeGeminiWorkoutGenerator(result=_valid_ai_workout_result())
    container.gemini_workout_generator_impl = generator
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.limitfallback@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        await _prefill_usage(
            ai_usage_context["session_factory"],
            user_id,
            ai_workout_count=3,
            total_ai_count=3,
        )
        response = await _generate_workout(client, token, "auto")

    usage = await _get_usage_counts(ai_usage_context["session_factory"], user_id)
    assert response["status_code"] == 200
    assert response["payload"]["data"]["source"] == "fallback"
    assert generator.called == 0
    assert usage is not None
    assert usage.ai_workout_count == 3
    assert usage.total_ai_count == 3


@pytest.mark.asyncio
async def test_ai_request_log_saved_on_success(ai_usage_context) -> None:
    app = ai_usage_context["app"]
    container.gemini_workout_generator_impl = FakeGeminiWorkoutGenerator(
        result=_valid_ai_workout_result()
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        user_id, token = await _register_and_login(
            client, "ai.usage.requestlog@example.com"
        )
        await _seed_profile_and_readiness(ai_usage_context["session_factory"], user_id)
        response = await _generate_workout(client, token, "gemini")

    requests = await _get_ai_requests(ai_usage_context["session_factory"], user_id)
    assert response["status_code"] == 200
    assert len(requests) == 1
    assert requests[0].provider == "openrouter"
    assert requests[0].model_name
    assert requests[0].status == "success"
