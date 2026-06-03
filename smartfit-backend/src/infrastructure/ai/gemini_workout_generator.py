import asyncio
import json
import logging
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
    AIConfigurationError,
    AIInvalidOutputError,
    AIProviderTimeoutError,
    AIRateLimitError,
    AIGenerationError,
)
from src.infrastructure.ai.gemini_prompt_builder import GeminiPromptBuilder
from src.infrastructure.ai.schema_validator import AIWorkoutSchemaValidator

logger = logging.getLogger(__name__)


class GeminiWorkoutGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        prompt_builder: GeminiPromptBuilder,
        schema_validator: AIWorkoutSchemaValidator,
        client: Any | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.schema_validator = schema_validator
        self._client = client

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            raise AIConfigurationError("Gemini API key is not configured.")

        prompt = self.prompt_builder.build_generate_workout_prompt(context)
        logger.info(
            "Calling Gemini workout generation for user %s with model=%s timeout=%ss allowed_exercises=%s prompt_chars=%s readiness_score=%s focus=%s equipment=%s avoid_exercises=%s allowed_slugs=%s",
            context.user_id,
            settings.GEMINI_MODEL,
            settings.GEMINI_TIMEOUT_SECONDS,
            len(context.allowed_exercises),
            len(prompt),
            context.readiness_score,
            context.focus_muscle,
            context.equipment,
            context.avoid_exercises,
            [item.slug for item in context.allowed_exercises],
        )
        logger.debug("Gemini workout prompt preview: %s", self._truncate(prompt, 1500))
        try:
            raw_text = await asyncio.wait_for(
                self._generate_content(prompt),
                timeout=settings.GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeoutError("Gemini request timed out.") from exc
        except AIRateLimitError:
            raise
        except AIGenerationError:
            raise
        except Exception as exc:
            raise AIGenerationError(f"Gemini provider error: {exc}") from exc

        logger.info(
            "Gemini workout raw response received for user %s chars=%s preview=%s",
            context.user_id,
            len(raw_text),
            self._truncate(raw_text, 1500),
        )

        try:
            raw_payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Gemini workout JSON parsing failed for user %s: %s raw_preview=%s",
                context.user_id,
                exc,
                self._truncate(raw_text, 1500),
            )
            raise AIInvalidOutputError("Gemini returned invalid JSON.") from exc

        logger.info(
            "Gemini workout JSON parsed for user %s keys=%s",
            context.user_id,
            (
                sorted(raw_payload.keys())
                if isinstance(raw_payload, dict)
                else type(raw_payload).__name__
            ),
        )

        try:
            result = self.schema_validator.validate_workout_output(raw_payload)
        except AIInvalidOutputError as exc:
            logger.warning(
                "Gemini workout schema validation failed for user %s: %s parsed_payload=%s",
                context.user_id,
                exc,
                self._truncate(json.dumps(raw_payload, ensure_ascii=False), 2000),
            )
            raise

        logger.info(
            "Gemini workout schema validation passed for user %s title=%s decision=%s exercise_count=%s",
            context.user_id,
            result.workout_title,
            result.training_decision,
            len(result.exercises),
        )
        return result

    async def chat(self, context: AIChatContext) -> AIChatResult:
        raise NotImplementedError("Use GeminiAIChatGenerator for AI chat.")

    async def _generate_content(self, prompt: str) -> str:
        settings = get_settings()
        if self._client is not None:
            result = self._client.generate_content(
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
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
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
        logger.info("Gemini workout generation completed successfully.")
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
        raise AIInvalidOutputError("Gemini response does not contain usable text.")

    def _truncate(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return f"{value[:limit]}...<truncated>"
