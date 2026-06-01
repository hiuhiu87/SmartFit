from uuid import UUID

from pydantic import BaseModel, Field


class AIChatRequestSchema(BaseModel):
    workout_id: UUID
    current_workout_plan_exercise_id: UUID | None = None
    message: str = Field(min_length=1, max_length=1000)


class AIChatSuggestedActionSchema(BaseModel):
    type: str
    exercise_id: UUID | None = None
    exercise_name: str | None = None
    target_sets: int | None = None
    target_reps: str | None = None
    rest_seconds: int | None = None
    target_rpe: int | None = None
    reason: str | None = None


class AIChatResponseSchema(BaseModel):
    reply: str
    intent: str
    suggested_action: AIChatSuggestedActionSchema | None = None


class AIChatHistoryItemSchema(BaseModel):
    id: UUID
    role: str
    message: str
    suggested_action: AIChatSuggestedActionSchema | None = None
    workout_plan_exercise_id: UUID | None = None
    created_at: str | None = None


class AIChatHistoryResponseSchema(BaseModel):
    items: list[AIChatHistoryItemSchema]
    limit: int
    offset: int
    total: int


class AIUsageDataSchema(BaseModel):
    ai_workout_count: int
    ai_chat_count: int
    ai_replacement_count: int
    ai_weekly_report_count: int
    total_ai_count: int


class AIUsageLimitSchema(BaseModel):
    ai_workout_limit: int
    ai_chat_limit: int
    ai_replacement_limit: int
    ai_weekly_report_limit: int
    total_ai_limit: int


class AIUsageTodayResponseSchema(BaseModel):
    date: str
    plan: str
    usage: AIUsageDataSchema
    limits: AIUsageLimitSchema
