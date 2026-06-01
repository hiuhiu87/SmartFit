from src.domain.ai.entities import AIUsageDaily, AIUsageLimit
from src.domain.common.exceptions import AIUsageLimitExceededError


class AIUsagePolicy:
    def get_limit_for_plan(self, plan: str) -> AIUsageLimit:
        if plan == "premium":
            return AIUsageLimit(
                ai_workout_limit=30,
                ai_chat_limit=200,
                ai_replacement_limit=100,
                ai_weekly_report_limit=30,
                total_ai_limit=300,
            )
        return AIUsageLimit(
            ai_workout_limit=3,
            ai_chat_limit=20,
            ai_replacement_limit=10,
            ai_weekly_report_limit=3,
            total_ai_limit=30,
        )

    def ensure_within_limit(
        self, usage: AIUsageDaily | None, request_type: str, plan: str
    ) -> None:
        workout_count = usage.ai_workout_count if usage else 0
        chat_count = usage.ai_chat_count if usage else 0
        replacement_count = usage.ai_replacement_count if usage else 0
        weekly_report_count = usage.ai_weekly_report_count if usage else 0
        total_count = usage.total_ai_count if usage else 0
        limits = self.get_limit_for_plan(plan)

        if total_count >= limits.total_ai_limit:
            raise AIUsageLimitExceededError("Daily AI usage limit reached.")

        if request_type == "generate_workout" and workout_count >= limits.ai_workout_limit:
            raise AIUsageLimitExceededError("Daily AI workout limit reached.")
        if request_type == "chat" and chat_count >= limits.ai_chat_limit:
            raise AIUsageLimitExceededError("Daily AI chat limit reached.")
        if request_type == "replace_exercise" and replacement_count >= limits.ai_replacement_limit:
            raise AIUsageLimitExceededError("Daily AI replacement limit reached.")
        if request_type == "weekly_report" and weekly_report_count >= limits.ai_weekly_report_limit:
            raise AIUsageLimitExceededError("Daily AI weekly report limit reached.")
