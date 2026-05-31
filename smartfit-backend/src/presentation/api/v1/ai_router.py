from fastapi import APIRouter

from src.presentation.schemas.ai_schema import AIChatRequestSchema, AIChatResponseSchema
from src.presentation.schemas.common_schema import APIResponseSchema

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=APIResponseSchema[AIChatResponseSchema])
async def chat(payload: AIChatRequestSchema) -> APIResponseSchema[AIChatResponseSchema]:
    # TODO: call AI chat use case wired through AIClientPort and persistence ports.
    return APIResponseSchema(
        data=AIChatResponseSchema(
            message=f"Stub reply: {payload.message}", provider="stub"
        )
    )
