from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.container import container
from src.application.ai.commands import AIChatCommand
from src.application.ai.queries import GetAIChatHistoryQuery
from src.application.ai_usage.commands import GetAIUsageTodayQuery
from src.infrastructure.database.session import get_session
from src.infrastructure.security.current_user import get_current_user_id
from src.presentation.schemas.ai_schema import (
    AIChatHistoryItemSchema,
    AIChatHistoryResponseSchema,
    AIChatRequestSchema,
    AIChatResponseSchema,
    AIChatSuggestedActionSchema,
    AIUsageDataSchema,
    AIUsageLimitSchema,
    AIUsageTodayResponseSchema,
)
from src.presentation.schemas.common_schema import APIResponseSchema

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get(
    "/usage/today",
    response_model=APIResponseSchema[AIUsageTodayResponseSchema],
)
async def get_ai_usage_today(
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[AIUsageTodayResponseSchema]:
    result = await container.get_ai_usage_today_use_case(session).execute(
        GetAIUsageTodayQuery(
            user_id=user_id,
            target_date=datetime.now(timezone.utc).date(),
        )
    )
    return APIResponseSchema(
        data=AIUsageTodayResponseSchema(
            date=result.date.isoformat(),
            plan=result.plan,
            usage=AIUsageDataSchema(
                ai_workout_count=result.usage.ai_workout_count,
                ai_chat_count=result.usage.ai_chat_count,
                ai_replacement_count=result.usage.ai_replacement_count,
                ai_weekly_report_count=result.usage.ai_weekly_report_count,
                total_ai_count=result.usage.total_ai_count,
            ),
            limits=AIUsageLimitSchema(
                ai_workout_limit=result.limits.ai_workout_limit,
                ai_chat_limit=result.limits.ai_chat_limit,
                ai_replacement_limit=result.limits.ai_replacement_limit,
                ai_weekly_report_limit=result.limits.ai_weekly_report_limit,
                total_ai_limit=result.limits.total_ai_limit,
            ),
        )
    )


@router.get(
    "/chat/history",
    response_model=APIResponseSchema[AIChatHistoryResponseSchema],
)
async def get_chat_history(
    workout_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[AIChatHistoryResponseSchema]:
    result = await container.get_ai_chat_history_use_case(session).execute(
        GetAIChatHistoryQuery(
            user_id=user_id,
            workout_id=workout_id,
            limit=limit,
            offset=offset,
        )
    )
    return APIResponseSchema(
        data=AIChatHistoryResponseSchema(
            items=[
                AIChatHistoryItemSchema(
                    id=item.id,
                    role=item.role,
                    message=item.message,
                    suggested_action=(
                        AIChatSuggestedActionSchema(
                            type=item.suggested_action.type,
                            exercise_id=item.suggested_action.exercise_id,
                            exercise_name=item.suggested_action.exercise_name,
                            target_sets=item.suggested_action.target_sets,
                            target_reps=item.suggested_action.target_reps,
                            rest_seconds=item.suggested_action.rest_seconds,
                            target_rpe=item.suggested_action.target_rpe,
                            reason=item.suggested_action.reason,
                        )
                        if item.suggested_action is not None
                        else None
                    ),
                    workout_plan_exercise_id=item.workout_plan_exercise_id,
                    created_at=item.created_at.isoformat() if item.created_at else None,
                )
                for item in result.items
            ],
            limit=result.limit,
            offset=result.offset,
            total=result.total,
        )
    )


@router.post("/chat", response_model=APIResponseSchema[AIChatResponseSchema])
async def chat(
    payload: AIChatRequestSchema,
    user_id=Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[AIChatResponseSchema]:
    result = await container.get_ai_chat_use_case(session).execute(
        AIChatCommand(
            user_id=user_id,
            workout_id=payload.workout_id,
            current_workout_plan_exercise_id=payload.current_workout_plan_exercise_id,
            message=payload.message,
        )
    )
    await session.commit()
    return APIResponseSchema(
        data=AIChatResponseSchema(
            reply=result.reply,
            intent=result.intent,
            suggested_action=(
                AIChatSuggestedActionSchema(
                    type=result.suggested_action.type,
                    exercise_id=result.suggested_action.exercise_id,
                    exercise_name=result.suggested_action.exercise_name,
                    target_sets=result.suggested_action.target_sets,
                    target_reps=result.suggested_action.target_reps,
                    rest_seconds=result.suggested_action.rest_seconds,
                    target_rpe=result.suggested_action.target_rpe,
                    reason=result.suggested_action.reason,
                )
                if result.suggested_action is not None
                else None
            ),
        )
    )
