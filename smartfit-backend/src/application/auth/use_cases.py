from datetime import datetime, timezone
from uuid import uuid4

from src.application.auth.commands import (
    LoginCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
)
from src.application.auth.dto import AuthTokenDTO, AuthenticatedUserDTO
from src.domain.common.enums import AuthProvider
from src.domain.common.exceptions import UnauthorizedError, ValidationError
from src.domain.user.entities import User
from src.domain.user.repositories import UserRepository
from src.infrastructure.security.jwt_provider import JWTProvider
from src.infrastructure.security.password_hasher import PasswordHasher


class RegisterUserUseCase:
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def execute(self, command: RegisterUserCommand) -> AuthenticatedUserDTO:
        existing_user = await self.user_repository.get_by_email(command.email)
        if existing_user is not None:
            raise ValidationError("Email is already registered")

        now = datetime.now(timezone.utc)
        user = User(
            id=uuid4(),
            email=command.email,
            password_hash=self.password_hasher.hash(command.password),
            auth_provider=AuthProvider.EMAIL,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created_user = await self.user_repository.create(user)
        return AuthenticatedUserDTO(
            id=created_user.id,
            email=created_user.email,
            is_active=created_user.is_active,
        )


class LoginUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        jwt_provider: JWTProvider,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.jwt_provider = jwt_provider

    async def execute(self, command: LoginCommand) -> AuthTokenDTO:
        user = await self.user_repository.get_by_email(command.email)
        if user is None or user.password_hash is None:
            raise UnauthorizedError("Invalid email or password")
        if not self.password_hasher.verify(command.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        subject = str(user.id)
        return AuthTokenDTO(
            access_token=self.jwt_provider.create_access_token(subject),
            refresh_token=self.jwt_provider.create_refresh_token(subject),
        )


class RefreshTokenUseCase:
    def __init__(
        self, user_repository: UserRepository, jwt_provider: JWTProvider
    ) -> None:
        self.user_repository = user_repository
        self.jwt_provider = jwt_provider

    async def execute(self, command: RefreshTokenCommand) -> AuthTokenDTO:
        user_id = self.jwt_provider.get_subject(
            command.refresh_token, expected_type="refresh"
        )
        user = await self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is inactive or unavailable")

        subject = str(user.id)
        return AuthTokenDTO(
            access_token=self.jwt_provider.create_access_token(subject),
            refresh_token=self.jwt_provider.create_refresh_token(subject),
        )
