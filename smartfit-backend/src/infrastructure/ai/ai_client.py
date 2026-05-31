from src.domain.ai.ports import AIClientPort


class AIClient(AIClientPort):
    async def send(self, prompt: str) -> str:
        # TODO: integrate actual provider SDK behind port abstraction.
        return f"Stub AI response for prompt: {prompt[:50]}"
