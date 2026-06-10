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
    AIChatGenerationError,
    AIChatInvalidOutputError,
    AIProviderTimeoutError,
)
from src.infrastructure.ai.gemini_chat_prompt_builder import GeminiChatPromptBuilder
from src.infrastructure.ai.schema_validator import AIChatSchemaValidator

logger = logging.getLogger(__name__)


class OllamaAIChatGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        prompt_builder: GeminiChatPromptBuilder,
        schema_validator: AIChatSchemaValidator,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.schema_validator = schema_validator

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        raise NotImplementedError(
            "Use OllamaWorkoutGenerator for workout generation."
        )

    async def chat(self, context: AIChatContext) -> AIChatResult:
        settings = get_settings()
        prompt = self.prompt_builder.build_chat_prompt(context)
        logger.info(
            "Calling Ollama chat generation for user %s with model=%s url=%s prompt_chars=%s",
            context.user_id,
            settings.OLLAMA_MODEL,
            settings.OLLAMA_API_URL,
            len(prompt),
        )

        try:
            raw_text = await asyncio.wait_for(
                self._generate_content(prompt),
                timeout=settings.OPENROUTER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeoutError("Ollama chat request timed out.") from exc
        except Exception as exc:
            raise AIChatGenerationError(
                f"Ollama chat provider error: {exc}"
            ) from exc

        logger.info(
            "Ollama chat raw response received for user %s chars=%s",
            context.user_id,
            len(raw_text),
        )

        try:
            raw_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Ollama chat JSON parsing failed for user %s: %s raw=%s",
                context.user_id,
                exc,
                raw_text,
            )
            raise AIChatInvalidOutputError(
                "Ollama chat returned invalid JSON."
            ) from exc

        try:
            result = self.schema_validator.validate(raw_payload)
        except AIChatInvalidOutputError as exc:
            logger.warning(
                "Ollama chat validation failed for user %s: %s",
                context.user_id,
                exc,
            )
            raise
        return result

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
            raise AIProviderTimeoutError("Ollama chat request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AIChatGenerationError(f"Ollama HTTP error: {exc}") from exc

        if response.status_code >= 400:
            raise AIChatGenerationError(
                f"Ollama provider error {response.status_code}: {response.text}"
            )

        raw_text = response.text
        if not raw_text.strip():
            raise AIChatInvalidOutputError("Ollama response does not contain usable text.")
        return raw_text
