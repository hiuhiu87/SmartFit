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
from src.application.readiness.use_cases import (
    CalculateReadinessUseCase,
    GetReadinessHistoryUseCase,
    GetTodayReadinessUseCase,
)
from src.application.user.use_cases import (
    GetCurrentUserProfileUseCase,
    UpdateUserEquipmentUseCase,
    UpdateUserProfileUseCase,
)
from src.application.workout.use_cases import (
    CompleteWorkoutUseCase,
    GenerateWorkoutUseCase,
    GetWorkoutDetailUseCase,
    GetWorkoutHistoryUseCase,
    LogWorkoutSetUseCase,
    StartWorkoutUseCase,
)
from src.domain.ai.ports import AIWorkoutGeneratorPort
from src.domain.common.exceptions import AIConfigurationError
from src.domain.readiness.services import ReadinessCalculator
from src.domain.workout.services import (
    RuleBasedWorkoutGenerator,
    WorkoutSafetyPolicy,
    WorkoutVolumeCalculator,
)
from src.infrastructure.ai.gemini_prompt_builder import GeminiPromptBuilder
from src.infrastructure.ai.gemini_workout_generator import GeminiWorkoutGenerator
from src.infrastructure.ai.output_mapper import AIWorkoutOutputMapper
from src.infrastructure.ai.safety_validator import AIWorkoutSafetyValidator
from src.infrastructure.ai.schema_validator import AIWorkoutSchemaValidator
from src.infrastructure.repositories.exercise_repository import SQLModelExerciseRepository
from src.infrastructure.repositories.health_repository import SQLModelHealthRepository
from src.infrastructure.repositories.readiness_repository import SQLModelReadinessRepository
from src.infrastructure.repositories.user_repository import SQLModelUserRepository
from src.infrastructure.repositories.workout_repository import SQLModelWorkoutRepository
from src.infrastructure.repositories.progress_repository import SQLModelProgressRepository
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher
from src.domain.progress.services import ProgressCalculator


class Container:
    def __init__(self) -> None:
        self.readiness_calculator = ReadinessCalculator()
        self.password_hasher = PasswordHasher()
        self.jwt_provider = JWTProvider()
        self.workout_generator = RuleBasedWorkoutGenerator()
        self.workout_safety_policy = WorkoutSafetyPolicy()
        self.workout_volume_calculator = WorkoutVolumeCalculator()
        self.progress_calculator = ProgressCalculator()
        self.gemini_prompt_builder = GeminiPromptBuilder()
        self.ai_workout_schema_validator = AIWorkoutSchemaValidator()
        self.ai_workout_safety_validator = AIWorkoutSafetyValidator()
        self.ai_workout_output_mapper = AIWorkoutOutputMapper()
        self.gemini_workout_generator_impl: AIWorkoutGeneratorPort = GeminiWorkoutGenerator(
            self.gemini_prompt_builder,
            self.ai_workout_schema_validator,
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

    def get_progress_repository(
        self, session: AsyncSession
    ) -> SQLModelProgressRepository:
        return SQLModelProgressRepository(session)

    def list_exercises_use_case(
        self, session: AsyncSession
    ) -> ListExercisesUseCase:
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
            ai_safety_validator=self.ai_workout_safety_validator,
            ai_output_mapper=self.ai_workout_output_mapper,
            safety_policy=self.workout_safety_policy,
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

    def get_workout_detail_use_case(
        self, session: AsyncSession
    ) -> GetWorkoutDetailUseCase:
        return GetWorkoutDetailUseCase(self.get_workout_repository(session))

    def start_workout_use_case(self, session: AsyncSession) -> StartWorkoutUseCase:
        return StartWorkoutUseCase(self.get_workout_repository(session))

    def log_workout_set_use_case(
        self, session: AsyncSession
    ) -> LogWorkoutSetUseCase:
        return LogWorkoutSetUseCase(self.get_workout_repository(session))

    def complete_workout_use_case(
        self, session: AsyncSession
    ) -> CompleteWorkoutUseCase:
        return CompleteWorkoutUseCase(
            self.get_workout_repository(session), self.workout_volume_calculator
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


container = Container()
