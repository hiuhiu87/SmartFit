import pytest
import uuid
from unittest.mock import AsyncMock, patch
import httpx

from app.settings import get_settings
from src.infrastructure.ai.openrouter_workout_generator import OpenRouterWorkoutGenerator
from src.infrastructure.ai.openrouter_chat_generator import OpenRouterAIChatGenerator
from src.domain.common.exceptions import AIPaymentRequiredError
from src.infrastructure.ai.gemini_prompt_builder import GeminiPromptBuilder
from src.infrastructure.ai.gemini_chat_prompt_builder import GeminiChatPromptBuilder
from src.infrastructure.ai.schema_validator import AIWorkoutSchemaValidator, AIChatSchemaValidator
from src.domain.ai.entities import AIWorkoutGenerationContext, AIAllowedExercise, AIChatContext


@pytest.mark.asyncio
async def test_workout_generator_fallback_success(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "auto")
    get_settings.cache_clear()

    mock_response_402 = AsyncMock(spec=httpx.Response)
    mock_response_402.status_code = 402
    mock_response_402.text = "This request requires more credits"

    mock_response_200 = AsyncMock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"workout_title": "Chest Day", "training_decision": "normal_volume", "estimated_duration_minutes": 45, "exercises": [{"exercise_slug": "dumbbell-press", "sets": 3, "reps": "8-10", "rest_seconds": 90, "rpe": 7, "notes": "test"}], "reasoning_summary": "test", "safety_note": "test"}'
                }
            }
        ]
    }

    called_payloads = []

    async def mock_post(url, headers, json):
        called_payloads.append(json)
        if json["model"] == "auto":
            return mock_response_402
        else:
            return mock_response_200

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        generator = OpenRouterWorkoutGenerator(
            prompt_builder=GeminiPromptBuilder(),
            schema_validator=AIWorkoutSchemaValidator(),
        )
        context = AIWorkoutGenerationContext(
            user_id="user-123",
            target_date="2026-06-10",
            goal="strength",
            training_level="beginner",
            readiness_score=80,
            readiness_category="good",
            readiness_recommendation="train_normal",
            workout_split="push",
            focus_muscle="chest",
            available_time_minutes=45,
            equipment=["dumbbell"],
            avoid_exercises=[],
            allowed_exercises=[
                AIAllowedExercise(
                    exercise_id="ex-1",
                    name="Dumbbell Press",
                    slug="dumbbell-press",
                    primary_muscle="chest",
                    equipment="dumbbell",
                    difficulty="beginner",
                    movement_type="compound",
                    movement_pattern="horizontal_push",
                    exercise_role="primary",
                )
            ],
        )
        result = await generator.generate_workout(context)

    assert result.workout_title == "Chest Day"
    assert len(called_payloads) == 2
    assert called_payloads[0]["model"] == "auto"
    assert called_payloads[1]["model"] == "google/gemini-2.5-flash:free"


@pytest.mark.asyncio
async def test_workout_generator_fallback_all_fail(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "auto")
    get_settings.cache_clear()

    mock_response_402 = AsyncMock(spec=httpx.Response)
    mock_response_402.status_code = 402
    mock_response_402.text = "This request requires more credits"

    called_payloads = []

    async def mock_post(url, headers, json):
        called_payloads.append(json)
        return mock_response_402

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        generator = OpenRouterWorkoutGenerator(
            prompt_builder=GeminiPromptBuilder(),
            schema_validator=AIWorkoutSchemaValidator(),
        )
        context = AIWorkoutGenerationContext(
            user_id="user-123",
            target_date="2026-06-10",
            goal="strength",
            training_level="beginner",
            readiness_score=80,
            readiness_category="good",
            readiness_recommendation="train_normal",
            workout_split="push",
            focus_muscle="chest",
            available_time_minutes=45,
            equipment=["dumbbell"],
            avoid_exercises=[],
            allowed_exercises=[],
        )
        with pytest.raises(AIPaymentRequiredError):
            await generator.generate_workout(context)

    # auto, then 3 fallback models tried
    assert len(called_payloads) == 4
    assert called_payloads[0]["model"] == "auto"
    assert called_payloads[1]["model"] == "google/gemini-2.5-flash:free"
    assert called_payloads[2]["model"] == "meta-llama/llama-3-8b-instruct:free"
    assert called_payloads[3]["model"] == "google/gemma-2-9b-it:free"


@pytest.mark.asyncio
async def test_chat_generator_fallback_success(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "auto")
    get_settings.cache_clear()

    mock_response_402 = AsyncMock(spec=httpx.Response)
    mock_response_402.status_code = 402
    mock_response_402.text = "This request requires more credits"

    mock_response_200 = AsyncMock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"reply": "Sure, I can help with that.", "intent": "general_workout_question"}'
                }
            }
        ]
    }

    called_payloads = []

    async def mock_post(url, headers, json):
        called_payloads.append(json)
        if json["model"] == "auto":
            return mock_response_402
        else:
            return mock_response_200

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        generator = OpenRouterAIChatGenerator(
            prompt_builder=GeminiChatPromptBuilder(),
            schema_validator=AIChatSchemaValidator(),
        )
        context = AIChatContext(
            user_id=uuid.uuid4(),
            workout_id=uuid.uuid4(),
            current_workout_plan_exercise_id=None,
            user_message="hello",
        )
        result = await generator.chat(context)

    assert result.reply == "Sure, I can help with that."
    assert result.intent == "general_workout_question"
    assert len(called_payloads) == 2
    assert called_payloads[0]["model"] == "auto"
    assert called_payloads[1]["model"] == "google/gemini-2.5-flash:free"
