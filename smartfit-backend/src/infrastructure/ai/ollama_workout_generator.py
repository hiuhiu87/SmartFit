import asyncio
import json
import logging
from typing import Any

import httpx

from app.settings import get_settings
from src.domain.ai.entities import (
    AIChatContext,
    AIChatResult,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)
from src.domain.ai.ports import AIWorkoutGeneratorPort
from src.domain.common.exceptions import (
    AIGenerationError,
    AIInvalidOutputError,
    AIProviderTimeoutError,
)
from src.infrastructure.ai.gemini_prompt_builder import GeminiPromptBuilder
from src.infrastructure.ai.schema_validator import AIWorkoutSchemaValidator

logger = logging.getLogger(__name__)


class OllamaWorkoutGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        prompt_builder: GeminiPromptBuilder,
        schema_validator: AIWorkoutSchemaValidator,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.schema_validator = schema_validator

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        settings = get_settings()
        prompt = self.prompt_builder.build_generate_workout_prompt(context)
        logger.info(
            "Calling Ollama workout generation for user %s with model=%s url=%s allowed_exercises=%s prompt_chars=%s",
            context.user_id,
            settings.OLLAMA_MODEL,
            settings.OLLAMA_API_URL,
            len(context.allowed_exercises),
            len(prompt),
        )

        try:
            raw_text = await asyncio.wait_for(
                self._generate_content(prompt),
                timeout=settings.OPENROUTER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeoutError("Ollama request timed out.") from exc
        except Exception as exc:
            raise AIGenerationError(f"Ollama provider error: {exc}") from exc

        logger.info(
            "Ollama workout raw response received for user %s chars=%s",
            context.user_id,
            len(raw_text),
        )

        try:
            raw_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Ollama workout JSON parsing failed for user %s: %s raw=%s",
                context.user_id,
                exc,
                raw_text,
            )
            raise AIInvalidOutputError("Ollama returned invalid JSON.") from exc

        try:
            result = self.schema_validator.validate_workout_output(raw_payload)
        except AIInvalidOutputError as exc:
            logger.warning(
                "Ollama workout schema validation failed for user %s: %s",
                context.user_id,
                exc,
            )
            raise
        return result

    async def chat(self, context: AIChatContext) -> AIChatResult:
        raise NotImplementedError("Use OllamaAIChatGenerator for AI chat.")

    async def _generate_content(self, prompt: str) -> str:
        settings = get_settings()
        payload = {
            "prompt": prompt,
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.OPENROUTER_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(
                    settings.OLLAMA_API_URL,
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError("Ollama request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AIGenerationError(f"Ollama HTTP error: {exc}") from exc

        if response.status_code >= 400:
            raise AIGenerationError(
                f"Ollama provider error {response.status_code}: {response.text}"
            )

        raw_text = response.text
        if not raw_text.strip():
            raise AIInvalidOutputError("Ollama response does not contain usable text.")
        return raw_text
