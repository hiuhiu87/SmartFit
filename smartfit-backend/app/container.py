from src.application.ai.use_cases import AIChatUseCase, GetAIChatHistoryUseCase
from src.application.ai_usage.use_cases import AIUsageService, GetAIUsageTodayUseCase
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.use_cases import (
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from src.application.exercise.use_cases import (
    GetExerciseByIdUseCase,
    ListExercisesUseCase,
)
from src.application.health.use_cases import (
    GetLatestHealthSummaryUseCase,
    SaveHealthSummaryUseCase,
    SaveManualCheckinUseCase,
)
from src.application.progress.use_cases import (
    GetPersonalRecordsUseCase,
    GetProgressOverviewUseCase,
    GetWeeklyReportUseCase,
)
from src.application.program.generator import ProgramWorkoutGenerator
from src.application.program.use_cases import ProgramService
from src.application.readiness.use_cases import (
    CalculateReadinessUseCase,
    GetReadinessHistoryUseCase,
    GetTodayReadinessUseCase,
)
from src.application.training.use_cases import GetTodayTrainingContextUseCase
from src.application.user.use_cases import (
    GetCurrentUserProfileUseCase,
    UpdateUserEquipmentUseCase,
    UpdateUserProfileUseCase,
)
from src.application.workout.use_cases import (
    ApplyExerciseReplacementUseCase,
    CompleteWorkoutUseCase,
    GenerateWorkoutUseCase,
    GetWorkoutDetailUseCase,
    GetWorkoutHistoryUseCase,
    LogWorkoutSetUseCase,
    StartWorkoutUseCase,
    SuggestExerciseReplacementUseCase,
)
from src.domain.ai.ports import AIWorkoutGeneratorPort
from src.domain.ai.services import AIUsagePolicy
from src.domain.progression.services import ProgressionService
from src.domain.program.services import ProgramScheduler, ProgramTemplateFactory
from src.domain.readiness.services import ReadinessCalculator
from src.domain.training.services import (
    ExercisePerformanceAnalyzer,
    MuscleFatigueCalculator,
    TrainingLoadCalculator,
    TrainingRecommendationService,
)
from src.domain.workout.services import (
    RuleBasedWorkoutGenerator,
    WorkoutSafetyPolicy,
    WorkoutVolumeCalculator,
)
from src.infrastructure.ai.gemini_chat_prompt_builder import GeminiChatPromptBuilder
from src.infrastructure.ai.gemini_prompt_builder import GeminiPromptBuilder
from src.infrastructure.ai.openrouter_chat_generator import OpenRouterAIChatGenerator
from src.infrastructure.ai.openrouter_workout_generator import (
    OpenRouterWorkoutGenerator,
)
from src.infrastructure.ai.output_mapper import AIWorkoutOutputMapper
from src.infrastructure.ai.safety_validator import (
    AIChatSafetyValidator,
    AIWorkoutSafetyValidator,
)
from src.infrastructure.ai.schema_validator import (
    AIChatSchemaValidator,
    AIWorkoutSchemaValidator,
)
from src.infrastructure.repositories.ai_repository import SQLModelAIRequestRepository
from src.infrastructure.repositories.ai_usage_repository import (
    SQLModelAIUsageRepository,
)
from src.infrastructure.repositories.exercise_repository import (
    SQLModelExerciseRepository,
)
from src.infrastructure.repositories.health_repository import SQLModelHealthRepository
from src.infrastructure.repositories.readiness_repository import (
    SQLModelReadinessRepository,
)
from src.infrastructure.repositories.user_repository import SQLModelUserRepository
from src.infrastructure.repositories.workout_repository import SQLModelWorkoutRepository
from src.infrastructure.repositories.progress_repository import (
    SQLModelProgressRepository,
)
from src.infrastructure.repositories.progression_repository import (
    SQLModelProgressionRepository,
)
from src.infrastructure.repositories.program_repository import SQLModelProgramRepository
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher
from src.domain.progress.services import ProgressCalculator
from src.infrastructure.repositories.subscription_repository import (
    SQLModelSubscriptionRepository,
)
from src.infrastructure.repositories.training_repository import (
    SQLModelTrainingRepository,
)


class Container:
    def __init__(self) -> None:
        self.readiness_calculator = ReadinessCalculator()
        self.password_hasher = PasswordHasher()
        self.jwt_provider = JWTProvider()
        self.progression_service = ProgressionService()
        self.program_template_factory = ProgramTemplateFactory()
        self.program_scheduler = ProgramScheduler()
        self.workout_generator = RuleBasedWorkoutGenerator(
            progression_service=self.progression_service
        )
        self.workout_safety_policy = WorkoutSafetyPolicy()
        self.workout_volume_calculator = WorkoutVolumeCalculator()
        self.progress_calculator = ProgressCalculator()
        self.exercise_performance_analyzer = ExercisePerformanceAnalyzer()
        self.ai_usage_policy = AIUsagePolicy()
        self.gemini_prompt_builder = GeminiPromptBuilder()
        self.gemini_chat_prompt_builder = GeminiChatPromptBuilder()
        self.ai_workout_schema_validator = AIWorkoutSchemaValidator()
        self.ai_chat_schema_validator = AIChatSchemaValidator()
        self.ai_workout_safety_validator = AIWorkoutSafetyValidator()
        self.ai_chat_safety_validator = AIChatSafetyValidator()
        self.ai_workout_output_mapper = AIWorkoutOutputMapper()
        self.gemini_workout_generator_impl: AIWorkoutGeneratorPort = (
            OpenRouterWorkoutGenerator(
                self.gemini_prompt_builder,
                self.ai_workout_schema_validator,
            )
        )
        self.gemini_ai_chat_generator_impl: AIWorkoutGeneratorPort = (
            OpenRouterAIChatGenerator(
                self.gemini_chat_prompt_builder,
                self.ai_chat_schema_validator,
            )
        )

    def register_user_use_case(self, session: AsyncSession) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            SQLModelUserRepository(session), self.password_hasher
        )

    def login_use_case(self, session: AsyncSession) -> LoginUseCase:
        return LoginUseCase(
            SQLModelUserRepository(session), self.password_hasher, self.jwt_provider
        )

    def refresh_token_use_case(self, session: AsyncSession) -> RefreshTokenUseCase:
        return RefreshTokenUseCase(SQLModelUserRepository(session), self.jwt_provider)

    def get_current_user_use_case(
        self, session: AsyncSession
    ) -> GetCurrentUserProfileUseCase:
        return GetCurrentUserProfileUseCase(SQLModelUserRepository(session))

    def update_profile_use_case(
        self, session: AsyncSession
    ) -> UpdateUserProfileUseCase:
        return UpdateUserProfileUseCase(SQLModelUserRepository(session))

    def update_equipment_use_case(
        self, session: AsyncSession
    ) -> UpdateUserEquipmentUseCase:
        return UpdateUserEquipmentUseCase(SQLModelUserRepository(session))

    def get_exercise_repository(
        self, session: AsyncSession
    ) -> SQLModelExerciseRepository:
        return SQLModelExerciseRepository(session)

    def get_user_repository(self, session: AsyncSession) -> SQLModelUserRepository:
        return SQLModelUserRepository(session)

    def get_readiness_repository(
        self, session: AsyncSession
    ) -> SQLModelReadinessRepository:
        return SQLModelReadinessRepository(session)

    def get_workout_repository(
        self, session: AsyncSession
    ) -> SQLModelWorkoutRepository:
        return SQLModelWorkoutRepository(session)

    def get_training_repository(
        self, session: AsyncSession
    ) -> SQLModelTrainingRepository:
        return SQLModelTrainingRepository(session)

    def get_training_recommendation_service(
        self, session: AsyncSession
    ) -> TrainingRecommendationService:
        repository = self.get_training_repository(session)
        return TrainingRecommendationService(
            load_calculator=TrainingLoadCalculator(repository),
            fatigue_calculator=MuscleFatigueCalculator(repository),
            performance_analyzer=self.exercise_performance_analyzer,
        )

    def get_progress_repository(
        self, session: AsyncSession
    ) -> SQLModelProgressRepository:
        return SQLModelProgressRepository(session)

    def get_program_repository(
        self, session: AsyncSession
    ) -> SQLModelProgramRepository:
        return SQLModelProgramRepository(session)

    def program_service(self, session: AsyncSession) -> ProgramService:
        repository = self.get_program_repository(session)
        return ProgramService(
            repository=repository,
            user_repository=self.get_user_repository(session),
            template_factory=self.program_template_factory,
            scheduler=self.program_scheduler,
            workout_generator=ProgramWorkoutGenerator(
                self.generate_workout_use_case(session), repository
            ),
        )

    def get_progression_repository(
        self, session: AsyncSession
    ) -> SQLModelProgressionRepository:
        return SQLModelProgressionRepository(session)

    def get_ai_request_repository(
        self, session: AsyncSession
    ) -> SQLModelAIRequestRepository:
        return SQLModelAIRequestRepository(session)

    def get_ai_usage_repository(
        self, session: AsyncSession
    ) -> SQLModelAIUsageRepository:
        return SQLModelAIUsageRepository(session)

    def get_subscription_repository(
        self, session: AsyncSession
    ) -> SQLModelSubscriptionRepository:
        return SQLModelSubscriptionRepository(session)

    def get_ai_usage_service(self, session: AsyncSession) -> AIUsageService:
        return AIUsageService(
            usage_repository=self.get_ai_usage_repository(session),
            usage_policy=self.ai_usage_policy,
            subscription_repository=self.get_subscription_repository(session),
        )

    def list_exercises_use_case(self, session: AsyncSession) -> ListExercisesUseCase:
        return ListExercisesUseCase(self.get_exercise_repository(session))

    def get_exercise_by_id_use_case(
        self, session: AsyncSession
    ) -> GetExerciseByIdUseCase:
        return GetExerciseByIdUseCase(self.get_exercise_repository(session))

    def save_health_summary_use_case(
        self, session: AsyncSession
    ) -> SaveHealthSummaryUseCase:
        return SaveHealthSummaryUseCase(SQLModelHealthRepository(session))

    def save_manual_checkin_use_case(
        self, session: AsyncSession
    ) -> SaveManualCheckinUseCase:
        return SaveManualCheckinUseCase(SQLModelHealthRepository(session))

    def get_latest_health_summary_use_case(
        self, session: AsyncSession
    ) -> GetLatestHealthSummaryUseCase:
        return GetLatestHealthSummaryUseCase(SQLModelHealthRepository(session))

    def calculate_readiness_use_case(
        self, session: AsyncSession
    ) -> CalculateReadinessUseCase:
        return CalculateReadinessUseCase(
            SQLModelReadinessRepository(session),
            SQLModelHealthRepository(session),
            self.readiness_calculator,
            TrainingLoadCalculator(self.get_training_repository(session)),
        )

    def get_today_readiness_use_case(
        self, session: AsyncSession
    ) -> GetTodayReadinessUseCase:
        calculate_use_case = self.calculate_readiness_use_case(session)
        return GetTodayReadinessUseCase(
            SQLModelReadinessRepository(session),
            calculate_use_case,
            SQLModelHealthRepository(session),
        )

    def get_readiness_history_use_case(
        self, session: AsyncSession
    ) -> GetReadinessHistoryUseCase:
        return GetReadinessHistoryUseCase(SQLModelReadinessRepository(session))

    def generate_workout_use_case(
        self, session: AsyncSession
    ) -> GenerateWorkoutUseCase:
        return GenerateWorkoutUseCase(
            user_repository=self.get_user_repository(session),
            readiness_repository=self.get_readiness_repository(session),
            exercise_repository=self.get_exercise_repository(session),
            workout_repository=self.get_workout_repository(session),
            generator=self.workout_generator,
            ai_generator=self.get_gemini_workout_generator(),
            ai_usage_service=self.get_ai_usage_service(session),
            ai_safety_validator=self.ai_workout_safety_validator,
            ai_output_mapper=self.ai_workout_output_mapper,
            safety_policy=self.workout_safety_policy,
            training_service=self.get_training_recommendation_service(session),
            progression_repository=self.get_progression_repository(session),
        )

    def get_today_training_context_use_case(
        self, session: AsyncSession
    ) -> GetTodayTrainingContextUseCase:
        return GetTodayTrainingContextUseCase(
            self.get_training_recommendation_service(session)
        )

    def get_gemini_prompt_builder(self) -> GeminiPromptBuilder:
        return self.gemini_prompt_builder

    def get_ai_workout_schema_validator(self) -> AIWorkoutSchemaValidator:
        return self.ai_workout_schema_validator

    def get_ai_workout_safety_validator(self) -> AIWorkoutSafetyValidator:
        return self.ai_workout_safety_validator

    def get_ai_workout_output_mapper(self) -> AIWorkoutOutputMapper:
        return self.ai_workout_output_mapper

    def get_gemini_workout_generator(self) -> AIWorkoutGeneratorPort:
        return self.gemini_workout_generator_impl

    def get_gemini_chat_prompt_builder(self) -> GeminiChatPromptBuilder:
        return self.gemini_chat_prompt_builder

    def get_ai_chat_schema_validator(self) -> AIChatSchemaValidator:
        return self.ai_chat_schema_validator

    def get_ai_chat_safety_validator(self) -> AIChatSafetyValidator:
        return self.ai_chat_safety_validator

    def get_gemini_ai_chat_generator(self) -> AIWorkoutGeneratorPort:
        return self.gemini_ai_chat_generator_impl

    def get_workout_detail_use_case(
        self, session: AsyncSession
    ) -> GetWorkoutDetailUseCase:
        return GetWorkoutDetailUseCase(self.get_workout_repository(session))

    def start_workout_use_case(self, session: AsyncSession) -> StartWorkoutUseCase:
        return StartWorkoutUseCase(
            self.get_workout_repository(session),
            self.get_program_repository(session),
        )

    def log_workout_set_use_case(self, session: AsyncSession) -> LogWorkoutSetUseCase:
        return LogWorkoutSetUseCase(self.get_workout_repository(session))

    def suggest_exercise_replacement_use_case(
        self, session: AsyncSession
    ) -> SuggestExerciseReplacementUseCase:
        return SuggestExerciseReplacementUseCase(
            self.get_workout_repository(session),
            self.get_exercise_repository(session),
            self.get_user_repository(session),
        )

    def apply_exercise_replacement_use_case(
        self, session: AsyncSession
    ) -> ApplyExerciseReplacementUseCase:
        return ApplyExerciseReplacementUseCase(
            self.get_workout_repository(session),
            self.get_exercise_repository(session),
        )

    def complete_workout_use_case(
        self, session: AsyncSession
    ) -> CompleteWorkoutUseCase:
        return CompleteWorkoutUseCase(
            self.get_workout_repository(session),
            self.workout_volume_calculator,
            self.get_program_repository(session),
        )

    def get_workout_history_use_case(
        self, session: AsyncSession
    ) -> GetWorkoutHistoryUseCase:
        return GetWorkoutHistoryUseCase(self.get_workout_repository(session))

    def get_progress_overview_use_case(
        self, session: AsyncSession
    ) -> GetProgressOverviewUseCase:
        return GetProgressOverviewUseCase(
            self.get_progress_repository(session),
            self.get_user_repository(session),
            self.progress_calculator,
        )

    def get_personal_records_use_case(
        self, session: AsyncSession
    ) -> GetPersonalRecordsUseCase:
        return GetPersonalRecordsUseCase(
            self.get_progress_repository(session), self.progress_calculator
        )

    def get_weekly_report_use_case(
        self, session: AsyncSession
    ) -> GetWeeklyReportUseCase:
        return GetWeeklyReportUseCase(
            self.get_progress_overview_use_case(session), self.progress_calculator
        )

    def get_ai_chat_use_case(self, session: AsyncSession) -> AIChatUseCase:
        return AIChatUseCase(
            user_repository=self.get_user_repository(session),
            readiness_repository=self.get_readiness_repository(session),
            exercise_repository=self.get_exercise_repository(session),
            workout_repository=self.get_workout_repository(session),
            ai_request_repository=self.get_ai_request_repository(session),
            ai_chat_generator=self.get_gemini_ai_chat_generator(),
            ai_chat_safety_validator=self.get_ai_chat_safety_validator(),
            ai_usage_service=self.get_ai_usage_service(session),
        )

    def get_ai_chat_history_use_case(
        self, session: AsyncSession
    ) -> GetAIChatHistoryUseCase:
        return GetAIChatHistoryUseCase(
            workout_repository=self.get_workout_repository(session),
            ai_request_repository=self.get_ai_request_repository(session),
        )

    def get_ai_usage_today_use_case(
        self, session: AsyncSession
    ) -> GetAIUsageTodayUseCase:
        return GetAIUsageTodayUseCase(self.get_ai_usage_service(session))


container = Container()
