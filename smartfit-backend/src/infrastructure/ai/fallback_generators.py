import logging
from src.domain.ai.entities import (
    AIChatContext,
    AIChatResult,
    AIWorkoutGenerationContext,
    AIWorkoutGenerationResult,
)
from src.domain.ai.ports import AIWorkoutGeneratorPort
from src.infrastructure.ai.ollama_workout_generator import OllamaWorkoutGenerator
from src.infrastructure.ai.openrouter_workout_generator import OpenRouterWorkoutGenerator
from src.infrastructure.ai.ollama_chat_generator import OllamaAIChatGenerator
from src.infrastructure.ai.openrouter_chat_generator import OpenRouterAIChatGenerator

logger = logging.getLogger(__name__)


class FallbackWorkoutGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        ollama_generator: OllamaWorkoutGenerator,
        openrouter_generator: OpenRouterWorkoutGenerator,
    ) -> None:
        self.ollama_generator = ollama_generator
        self.openrouter_generator = openrouter_generator

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        try:
            logger.info("Attempting workout generation with primary Ollama generator...")
            return await self.ollama_generator.generate_workout(context)
        except Exception as exc:
            logger.warning(
                "Ollama workout generation failed: %s. Falling back to OpenRouter...",
                exc,
                exc_info=True,
            )
            try:
                return await self.openrouter_generator.generate_workout(context)
            except Exception as inner_exc:
                inner_exc.provider = "openrouter"
                raise inner_exc

    async def chat(self, context: AIChatContext) -> AIChatResult:
        raise NotImplementedError("Use FallbackAIChatGenerator for chat.")


class FallbackAIChatGenerator(AIWorkoutGeneratorPort):
    def __init__(
        self,
        ollama_generator: OllamaAIChatGenerator,
        openrouter_generator: OpenRouterAIChatGenerator,
    ) -> None:
        self.ollama_generator = ollama_generator
        self.openrouter_generator = openrouter_generator

    async def generate_workout(
        self, context: AIWorkoutGenerationContext
    ) -> AIWorkoutGenerationResult:
        raise NotImplementedError("Use FallbackWorkoutGenerator for workout generation.")

    async def chat(self, context: AIChatContext) -> AIChatResult:
        try:
            logger.info("Attempting AI chat with primary Ollama generator...")
            return await self.ollama_generator.chat(context)
        except Exception as exc:
            logger.warning(
                "Ollama AI chat failed: %s. Falling back to OpenRouter...",
                exc,
                exc_info=True,
            )
            try:
                return await self.openrouter_generator.chat(context)
            except Exception as inner_exc:
                inner_exc.provider = "openrouter"
                raise inner_exc
