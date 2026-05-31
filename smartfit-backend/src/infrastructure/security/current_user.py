from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.exceptions import UnauthorizedError
from src.domain.user.entities import User
from src.infrastructure.database.session import get_session
from src.infrastructure.repositories.user_repository import SQLModelUserRepository
from src.infrastructure.security.jwt_provider import JWTProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    provider = JWTProvider()
    user_id = provider.get_subject(token, expected_type="access")
    repository = SQLModelUserRepository(session)
    user = await repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Authenticated user is not available")
    return user


async def get_current_user_id(current_user: User = Depends(get_current_user)):
    return current_user.id
