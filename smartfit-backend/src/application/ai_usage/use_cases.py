from datetime import datetime, timezone

from src.application.ai_usage.commands import (
    CheckAIUsageLimitCommand,
    GetAIUsageTodayQuery,
    RecordAIUsageCommand,
)
from src.application.ai_usage.dto import (
    AIUsageCountsDTO,
    AIUsageLimitsDTO,
    AIUsageTodayDTO,
)
from src.domain.ai.entities import AIRequestLog
from src.domain.common.enums import SubscriptionStatus
from src.domain.ai.repositories import AIUsageRepository
from src.domain.ai.services import AIUsagePolicy
from src.domain.subscription.repositories import SubscriptionRepository


class AIUsageService:
    def __init__(
        self,
        usage_repository: AIUsageRepository,
        usage_policy: AIUsagePolicy,
        subscription_repository: SubscriptionRepository | None = None,
    ) -> None:
        self.usage_repository = usage_repository
        self.usage_policy = usage_policy
        self.subscription_repository = subscription_repository

    async def get_plan(self, user_id) -> str:
        if self.subscription_repository is None:
            return "free"
        subscription = await self.subscription_repository.get_by_user_id(user_id)
        if subscription is None:
            return "free"
        if subscription.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        }:
            return "free"
        if (
            subscription.expires_at is not None
            and subscription.expires_at <= datetime.now(timezone.utc)
        ):
            return "free"
        return subscription.plan.value

    async def check_limit(self, command: CheckAIUsageLimitCommand) -> None:
        usage = await self.usage_repository.get_daily_usage(
            command.user_id, command.target_date
        )
        plan = await self.get_plan(command.user_id)
        self.usage_policy.ensure_within_limit(usage, command.request_type, plan)

    async def record(self, command: RecordAIUsageCommand) -> None:
        await self.usage_repository.increment_usage(
            command.user_id, command.target_date, command.request_type
        )
        await self.usage_repository.save_request_log(command.request_log)

    async def record_log_only(self, log: AIRequestLog) -> None:
        await self.usage_repository.save_request_log(log)


class GetAIUsageTodayUseCase:
    def __init__(self, usage_service: AIUsageService) -> None:
        self.usage_service = usage_service

    async def execute(self, query: GetAIUsageTodayQuery) -> AIUsageTodayDTO:
        plan = await self.usage_service.get_plan(query.user_id)
        usage = await self.usage_service.usage_repository.get_daily_usage(
            query.user_id, query.target_date
        )
        limits = self.usage_service.usage_policy.get_limit_for_plan(plan)
        return AIUsageTodayDTO(
            date=query.target_date,
            plan=plan,
            usage=AIUsageCountsDTO(
                ai_workout_count=usage.ai_workout_count if usage else 0,
                ai_chat_count=usage.ai_chat_count if usage else 0,
                ai_replacement_count=usage.ai_replacement_count if usage else 0,
                ai_weekly_report_count=usage.ai_weekly_report_count if usage else 0,
                total_ai_count=usage.total_ai_count if usage else 0,
            ),
            limits=AIUsageLimitsDTO(
                ai_workout_limit=limits.ai_workout_limit,
                ai_chat_limit=limits.ai_chat_limit,
                ai_replacement_limit=limits.ai_replacement_limit,
                ai_weekly_report_limit=limits.ai_weekly_report_limit,
                total_ai_limit=limits.total_ai_limit,
            ),
        )
