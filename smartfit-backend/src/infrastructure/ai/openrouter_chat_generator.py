import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

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
    AIConfigurationError,
    AIPaymentRequiredError,
    AIProviderTimeoutError,
    AIRateLimitError,
)
from src.infrastructure.ai.gemini_chat_prompt_builder import GeminiChatPromptBuilder
from src.infrastructure.ai.schema_validator import AIChatSchemaValidator


class OpenRouterAIChatGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        prompt_builder: GeminiChatPromptBuilder,
        schema_validator: AIChatSchemaValidator,
        client: Any | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.schema_validator = schema_validator
        self._client = client

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        raise NotImplementedError(
            "Use OpenRouterWorkoutGenerator for workout generation."
        )

    async def chat(self, context: AIChatContext) -> AIChatResult:
        settings = get_settings()
        if not settings.OPENROUTER_API_KEY:
            raise AIConfigurationError("OpenRouter API key is not configured.")

        prompt = self.prompt_builder.build_chat_prompt(context)
        try:
            raw_text = await asyncio.wait_for(
                self._generate_content(prompt),
                timeout=settings.OPENROUTER_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeoutError("OpenRouter chat request timed out.") from exc
        except AIRateLimitError:
            raise
        except AIChatGenerationError:
            raise
        except Exception as exc:
            raise AIChatGenerationError(
                f"OpenRouter chat provider error: {exc}"
            ) from exc

        try:
            raw_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AIChatInvalidOutputError(
                "OpenRouter chat returned invalid JSON."
            ) from exc

        result = self.schema_validator.validate(raw_payload)
        result.provider = "openrouter"
        return result

    async def _generate_content(self, prompt: str) -> str:
        settings = get_settings()
        if self._client is not None:
            result = self._client.chat_completion(
                model=settings.OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_output_tokens=min(settings.OPENROUTER_MAX_OUTPUT_TOKENS, 600),
            )
            if asyncio.iscoroutine(result):
                result = await result
            return self._extract_text(result)

        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": min(settings.OPENROUTER_MAX_OUTPUT_TOKENS, 600),
            "response_format": {"type": "json_object"},
        }
        try:
            response = await self._post_chat_completion(payload)
            return self._extract_text(response)
        except AIPaymentRequiredError as exc:
            logger.warning(
                "OpenRouter chat request failed with 402 Payment Required for model %s. Retrying with free fallback models...",
                settings.OPENROUTER_MODEL,
            )
            fallback_models = [
                "google/gemini-2.5-flash:free",
                "meta-llama/llama-3-8b-instruct:free",
                "google/gemma-2-9b-it:free",
            ]
            last_err = exc
            for model in fallback_models:
                logger.info("Retrying OpenRouter chat with free model: %s", model)
                fallback_payload = dict(payload)
                fallback_payload["model"] = model
                try:
                    response = await self._post_chat_completion(fallback_payload)
                    logger.info("OpenRouter chat completed successfully using fallback model %s.", model)
                    return self._extract_text(response)
                except AIPaymentRequiredError as fallback_exc:
                    last_err = fallback_exc
                    logger.warning("Fallback chat model %s failed with 402 Payment Required.", model)
                except Exception as fallback_exc:
                    last_err = fallback_exc
                    logger.warning("Fallback chat model %s failed: %s", model, fallback_exc)
            raise last_err

    async def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if settings.OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER
        if settings.OPENROUTER_APP_TITLE:
            headers["X-Title"] = settings.OPENROUTER_APP_TITLE

        try:
            async with httpx.AsyncClient(
                timeout=settings.OPENROUTER_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError("OpenRouter chat request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AIChatGenerationError(f"OpenRouter HTTP error: {exc}") from exc

        if response.status_code == 429:
            raise AIRateLimitError("OpenRouter rate limit or quota exceeded.")
        if response.status_code == 402:
            raise AIPaymentRequiredError(
                f"OpenRouter provider error 402: {response.text}"
            )
        if response.status_code >= 400:
            raise AIChatGenerationError(
                f"OpenRouter provider error {response.status_code}: {response.text}"
            )
        return response.json()

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, str) and response.strip():
            return response
        if isinstance(response, dict):
            choices = response.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    message = (
                        choice.get("message") if isinstance(choice, dict) else None
                    )
                    content = (
                        message.get("content") if isinstance(message, dict) else None
                    )
                    if isinstance(content, str) and content.strip():
                        return content
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text
        raise AIChatInvalidOutputError(
            "OpenRouter chat response does not contain usable text."
        )
