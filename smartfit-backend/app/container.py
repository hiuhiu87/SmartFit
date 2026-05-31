from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.use_cases import (
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from src.application.health.use_cases import (
    SaveHealthSummaryUseCase,
    SaveManualCheckinUseCase,
)
from src.application.progress.use_cases import (
    GetPersonalRecordsUseCase,
    GetProgressOverviewUseCase,
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
from src.domain.readiness.services import ReadinessCalculator
from src.infrastructure.ai.ai_client import AIClient
from src.infrastructure.repositories.user_repository import SQLModelUserRepository
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher


class Container:
    def __init__(self) -> None:
        self.readiness_calculator = ReadinessCalculator()
        self.ai_client = AIClient()
        self.password_hasher = PasswordHasher()
        self.jwt_provider = JWTProvider()

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

    def save_health_summary_use_case(self) -> SaveHealthSummaryUseCase:
        return SaveHealthSummaryUseCase()

    def save_manual_checkin_use_case(self) -> SaveManualCheckinUseCase:
        return SaveManualCheckinUseCase()

    def calculate_readiness_use_case(self) -> CalculateReadinessUseCase:
        return CalculateReadinessUseCase(self.readiness_calculator)

    def get_today_readiness_use_case(self) -> GetTodayReadinessUseCase:
        return GetTodayReadinessUseCase()

    def get_readiness_history_use_case(self) -> GetReadinessHistoryUseCase:
        return GetReadinessHistoryUseCase()

    def generate_workout_use_case(self) -> GenerateWorkoutUseCase:
        return GenerateWorkoutUseCase()

    def get_workout_detail_use_case(self) -> GetWorkoutDetailUseCase:
        return GetWorkoutDetailUseCase()

    def start_workout_use_case(self) -> StartWorkoutUseCase:
        return StartWorkoutUseCase()

    def log_workout_set_use_case(self) -> LogWorkoutSetUseCase:
        return LogWorkoutSetUseCase()

    def complete_workout_use_case(self) -> CompleteWorkoutUseCase:
        return CompleteWorkoutUseCase()

    def get_workout_history_use_case(self) -> GetWorkoutHistoryUseCase:
        return GetWorkoutHistoryUseCase()

    def get_progress_overview_use_case(self) -> GetProgressOverviewUseCase:
        return GetProgressOverviewUseCase()

    def get_personal_records_use_case(self) -> GetPersonalRecordsUseCase:
        return GetPersonalRecordsUseCase()


container = Container()
