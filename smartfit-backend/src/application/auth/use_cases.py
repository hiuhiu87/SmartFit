from uuid import uuid4

from src.application.auth.commands import LoginCommand, RegisterUserCommand
from src.application.auth.dto import AuthTokenDTO, AuthenticatedUserDTO


class RegisterUserUseCase:
    async def execute(self, command: RegisterUserCommand) -> AuthenticatedUserDTO:
        # TODO: persist user, hash password, and issue verification flow.
        return AuthenticatedUserDTO(id=uuid4(), email=command.email)


class LoginUseCase:
    async def execute(self, command: LoginCommand) -> AuthTokenDTO:
        # TODO: validate credentials against user repository and generate JWTs.
        return AuthTokenDTO(access_token=f"access-{command.email}", refresh_token=f"refresh-{command.email}")
