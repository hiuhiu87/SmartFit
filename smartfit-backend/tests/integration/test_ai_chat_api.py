from pathlib import Path
from datetime import date
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.container import container
from app.main import create_app
from src.domain.ai.entities import AIChatResult, AIChatSuggestedAction
from src.domain.common.enums import Goal, ReadinessCategory, ReadinessRecommendation, TrainingLevel
from src.domain.common.exceptions import AIProviderTimeoutError
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.models.ai_model import AIChatMessageModel, AIRequestModel
from src.infrastructure.database.models.ai_model import AIUsageDailyModel
from src.infrastructure.database.models.exercise_model import ExerciseAlternativeModel, ExerciseModel
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import UserEquipmentModel, UserModel, UserProfileModel
from src.infrastructure.database.models.workout_model import (
    WorkoutFeedbackModel,
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.seed.seed_exercises import _seed_rows


class FakeChatGenerator:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc

    async def chat(self, context):
        if self.exc is not None:
            raise self.exc
        return self.result

    async def generate_workout(self, context):
        raise NotImplementedError


@pytest_asyncio.fixture
async def ai_chat_context(tmp_path: Path):
    db_path = tmp_path / "ai_chat_test.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

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
                    AIUsageDailyModel.__table__,
                    AIRequestModel.__table__,
                    AIChatMessageModel.__table__,
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

    original_chat_generator = container.gemini_ai_chat_generator_impl
    yield {
        "app": app,
        "session_factory": session_factory,
        "original_chat_generator": original_chat_generator,
    }
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
    return register_response.json()["data"]["id"], login_response.json()["data"]["access_token"]


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
                full_name="AI Chat User",
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
    assert generated.status_code == 200
    workout = generated.json()["data"]
    started = await client.post(
        f"/api/v1/workouts/{workout['workout_id']}/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"started_at": "2026-06-01T18:00:00Z"},
    )
    assert started.status_code == 200
    workout["workout_log_id"] = started.json()["data"]["workout_log_id"]
    return workout


async def _get_exercise_id_by_slug(
    session_factory: async_sessionmaker[AsyncSession], slug: str
) -> str:
    async with session_factory() as session:
        result = await session.execute(select(ExerciseModel).where(ExerciseModel.slug == slug))
        model = result.scalar_one()
        return str(model.id)


@pytest.mark.asyncio
async def test_ai_chat_replace_exercise_success(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    replacement_id = await _get_exercise_id_by_slug(ai_chat_context["session_factory"], "push-up")
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="You can switch to Push-Up for 3 sets of 10-12 reps with 75 seconds rest.",
            intent="replace_exercise",
            suggested_action=AIChatSuggestedAction(
                type="replace_exercise",
                exercise_id=UUID(replacement_id),
                exercise_name="Push-Up",
                target_sets=3,
                target_reps="10-12",
                rest_seconds=75,
                target_rpe=7,
                reason="Similar chest focus with bodyweight equipment.",
            ),
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.replace@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        current_exercise_id = workout["exercises"][0]["workout_plan_exercise_id"]
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": current_exercise_id,
                "message": "The bench is taken. What can I do instead?",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["reply"]
    assert payload["intent"] == "replace_exercise"
    assert payload["suggested_action"]["type"] == "replace_exercise"
    assert payload["suggested_action"]["exercise_id"] == replacement_id


@pytest.mark.asyncio
async def test_ai_chat_does_not_auto_apply_replacement(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    replacement_id = await _get_exercise_id_by_slug(ai_chat_context["session_factory"], "push-up")
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Use Push-Up instead for now.",
            intent="replace_exercise",
            suggested_action=AIChatSuggestedAction(
                type="replace_exercise",
                exercise_id=UUID(replacement_id),
                exercise_name="Push-Up",
                target_sets=3,
                target_reps="10-12",
                rest_seconds=75,
                target_rpe=7,
                reason="Same muscle focus.",
            ),
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.noapply@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        current_exercise_id = workout["exercises"][0]["workout_plan_exercise_id"]
        await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": current_exercise_id,
                "message": "Need a replacement.",
            },
        )
        detail = await client.get(
            f"/api/v1/workouts/{workout['workout_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert detail.status_code == 200
    assert detail.json()["data"]["exercises"][0]["workout_plan_exercise_id"] == current_exercise_id


@pytest.mark.asyncio
async def test_ai_chat_pain_message_returns_safety_warning(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Stop or reduce this movement if your shoulder hurts. Rest and use a lighter option.",
            intent="safety_warning",
            suggested_action=None,
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.pain@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "My shoulder hurts during this exercise.",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["intent"] == "safety_warning"


@pytest.mark.asyncio
async def test_ai_chat_blocks_unknown_replacement_id(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Try this other exercise.",
            intent="replace_exercise",
            suggested_action=AIChatSuggestedAction(
                type="replace_exercise",
                exercise_id=UUID("11111111-1111-1111-1111-111111111111"),
                exercise_name="Unknown Movement",
                target_sets=3,
                target_reps="10-12",
                rest_seconds=75,
                target_rpe=7,
                reason="same muscle",
            ),
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.unknown@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "Need another option.",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["suggested_action"] is None


@pytest.mark.asyncio
async def test_ai_chat_user_cannot_chat_about_other_user_workout(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Use Push-Up.",
            intent="replace_exercise",
            suggested_action=None,
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_a_id, token_a = await _register_and_login(client, "ai.chat.owner.a@example.com")
        user_b_id, token_b = await _register_and_login(client, "ai.chat.owner.b@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_a_id)
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_b_id)
        workout = await _generate_and_start_workout(client, token_a)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "What should I do instead?",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ai_chat_message_saved(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    replacement_id = await _get_exercise_id_by_slug(ai_chat_context["session_factory"], "push-up")
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Switch to Push-Up.",
            intent="replace_exercise",
            suggested_action=AIChatSuggestedAction(
                type="replace_exercise",
                exercise_id=UUID(replacement_id),
                exercise_name="Push-Up",
                target_sets=3,
                target_reps="10-12",
                rest_seconds=75,
                target_rpe=7,
                reason="bodyweight chest option",
            ),
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.saved@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "Need a swap.",
            },
        )

    assert response.status_code == 200
    async with ai_chat_context["session_factory"]() as session:
        request_count = (
            await session.execute(select(func.count()).select_from(AIRequestModel))
        ).scalar_one()
        message_count = (
            await session.execute(select(func.count()).select_from(AIChatMessageModel))
        ).scalar_one()
    assert request_count == 1
    assert message_count == 2


@pytest.mark.asyncio
async def test_ai_chat_empty_message_validation(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(reply="ok", intent="general_workout_question")
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.empty@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "message": "",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_gemini_failure_returns_safe_fallback(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        exc=AIProviderTimeoutError("timeout")
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.fail@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        response = await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "The machine is busy.",
            },
        )

    assert response.status_code == 200
    assert "couldn't generate" in response.json()["data"]["reply"].lower()


@pytest.mark.asyncio
async def test_ai_chat_history_returns_saved_messages(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    replacement_id = await _get_exercise_id_by_slug(ai_chat_context["session_factory"], "push-up")
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(
            reply="Use Push-Up instead.",
            intent="replace_exercise",
            suggested_action=AIChatSuggestedAction(
                type="replace_exercise",
                exercise_id=UUID(replacement_id),
                exercise_name="Push-Up",
                target_sets=3,
                target_reps="10-12",
                rest_seconds=75,
                target_rpe=7,
                reason="Chest focus with bodyweight.",
            ),
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_id, token = await _register_and_login(client, "ai.chat.history@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_id)
        workout = await _generate_and_start_workout(client, token)
        await client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workout_id": workout["workout_id"],
                "current_workout_plan_exercise_id": workout["exercises"][0]["workout_plan_exercise_id"],
                "message": "Need a replacement.",
            },
        )
        history = await client.get(
            f"/api/v1/ai/chat/history?workout_id={workout['workout_id']}&limit=20&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert history.status_code == 200
    payload = history.json()["data"]
    assert payload["total"] == 2
    assert payload["items"][0]["role"] == "user"
    assert payload["items"][1]["role"] == "assistant"
    assert payload["items"][1]["suggested_action"]["type"] == "replace_exercise"


@pytest.mark.asyncio
async def test_ai_chat_history_user_cannot_access_other_user_workout(ai_chat_context) -> None:
    app = ai_chat_context["app"]
    container.gemini_ai_chat_generator_impl = FakeChatGenerator(
        result=AIChatResult(reply="ok", intent="general_workout_question")
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        user_a_id, token_a = await _register_and_login(client, "ai.chat.history.owner.a@example.com")
        user_b_id, token_b = await _register_and_login(client, "ai.chat.history.owner.b@example.com")
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_a_id)
        await _seed_profile_and_readiness(ai_chat_context["session_factory"], user_b_id)
        workout = await _generate_and_start_workout(client, token_a)
        history = await client.get(
            f"/api/v1/ai/chat/history?workout_id={workout['workout_id']}",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert history.status_code == 404
