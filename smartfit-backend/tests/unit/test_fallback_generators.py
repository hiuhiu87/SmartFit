import pytest
from unittest.mock import AsyncMock
from src.infrastructure.ai.fallback_generators import FallbackWorkoutGenerator, FallbackAIChatGenerator
from src.domain.ai.entities import AIWorkoutGenerationContext, AIChatContext, AIWorkoutGenerationResult, AIChatResult


@pytest.mark.asyncio
async def test_fallback_workout_generator_success_ollama() -> None:
    mock_ollama = AsyncMock()
    mock_openrouter = AsyncMock()

    mock_result = AsyncMock(spec=AIWorkoutGenerationResult)
    mock_ollama.generate_workout.return_value = mock_result

    fallback = FallbackWorkoutGenerator(mock_ollama, mock_openrouter)
    context = AsyncMock(spec=AIWorkoutGenerationContext)

    res = await fallback.generate_workout(context)

    assert res == mock_result
    mock_ollama.generate_workout.assert_called_once_with(context)
    mock_openrouter.generate_workout.assert_not_called()


@pytest.mark.asyncio
async def test_fallback_workout_generator_fallback_to_openrouter() -> None:
    mock_ollama = AsyncMock()
    mock_openrouter = AsyncMock()

    mock_ollama.generate_workout.side_effect = RuntimeError("Ollama down")
    mock_result = AsyncMock(spec=AIWorkoutGenerationResult)
    mock_openrouter.generate_workout.return_value = mock_result

    fallback = FallbackWorkoutGenerator(mock_ollama, mock_openrouter)
    context = AsyncMock(spec=AIWorkoutGenerationContext)

    res = await fallback.generate_workout(context)

    assert res == mock_result
    mock_ollama.generate_workout.assert_called_once_with(context)
    mock_openrouter.generate_workout.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_fallback_chat_generator_success_ollama() -> None:
    mock_ollama = AsyncMock()
    mock_openrouter = AsyncMock()

    mock_result = AsyncMock(spec=AIChatResult)
    mock_ollama.chat.return_value = mock_result

    fallback = FallbackAIChatGenerator(mock_ollama, mock_openrouter)
    context = AsyncMock(spec=AIChatContext)

    res = await fallback.chat(context)

    assert res == mock_result
    mock_ollama.chat.assert_called_once_with(context)
    mock_openrouter.chat.assert_not_called()


@pytest.mark.asyncio
async def test_fallback_chat_generator_fallback_to_openrouter() -> None:
    mock_ollama = AsyncMock()
    mock_openrouter = AsyncMock()

    mock_ollama.chat.side_effect = RuntimeError("Ollama down")
    mock_result = AsyncMock(spec=AIChatResult)
    mock_openrouter.chat.return_value = mock_result

    fallback = FallbackAIChatGenerator(mock_ollama, mock_openrouter)
    context = AsyncMock(spec=AIChatContext)

    res = await fallback.chat(context)

    assert res == mock_result
    mock_ollama.chat.assert_called_once_with(context)
    mock_openrouter.chat.assert_called_once_with(context)
