import asyncio
import json
from typing import Any

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
    AIProviderTimeoutError,
    AIRateLimitError,
)
from src.infrastructure.ai.gemini_chat_prompt_builder import GeminiChatPromptBuilder
from src.infrastructure.ai.schema_validator import AIChatSchemaValidator


class GeminiAIChatGenerator(AIWorkoutGeneratorPort):
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
        raise NotImplementedError("Use GeminiWorkoutGenerator for workout generation.")

    async def chat(self, context: AIChatContext) -> AIChatResult:
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            raise AIConfigurationError("Gemini API key is not configured.")

        prompt = self.prompt_builder.build_chat_prompt(context)
        try:
            raw_text = await asyncio.wait_for(
                self._generate_content(prompt),
                timeout=settings.GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeoutError("Gemini chat request timed out.") from exc
        except AIRateLimitError:
            raise
        except AIChatGenerationError:
            raise
        except Exception as exc:
            raise AIChatGenerationError(f"Gemini chat provider error: {exc}") from exc

        try:
            raw_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AIChatInvalidOutputError(
                "Gemini chat returned invalid JSON."
            ) from exc

        return self.schema_validator.validate(raw_payload)

    async def _generate_content(self, prompt: str) -> str:
        settings = get_settings()
        if self._client is not None:
            result = self._client.chat(
                model=settings.GEMINI_MODEL,
                prompt=prompt,
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            )
            if asyncio.iscoroutine(result):
                result = await result
            return self._extract_text(result)

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise AIConfigurationError(
                "google-genai package is not installed or cannot be imported."
            ) from exc

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=settings.GEMINI_TIMEOUT_SECONDS * 1000
            ),
        )

        def _call() -> Any:
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=min(settings.GEMINI_MAX_OUTPUT_TOKENS, 600),
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )

        try:
            response = await asyncio.to_thread(_call)
        except Exception as exc:
            text = str(exc).lower()
            if "429" in text or "rate limit" in text or "quota" in text:
                raise AIRateLimitError("Gemini rate limit or quota exceeded.") from exc
            raise
        return self._extract_text(response)

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text
        candidates = getattr(response, "candidates", None)
        if candidates:
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) if content is not None else None
                if parts:
                    for part in parts:
                        part_text = getattr(part, "text", None)
                        if isinstance(part_text, str) and part_text.strip():
                            return part_text
        raise AIChatInvalidOutputError(
            "Gemini chat response does not contain usable text."
        )
