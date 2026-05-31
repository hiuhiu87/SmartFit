from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class AuthTokenDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(slots=True)
class AuthenticatedUserDTO:
    id: UUID
    email: str
