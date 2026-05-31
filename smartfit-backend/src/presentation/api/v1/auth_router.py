from dataclasses import asdict

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import container
from src.application.auth.commands import (
    LoginCommand,
    RefreshTokenCommand,
    RegisterUserCommand,
)
from src.infrastructure.database.session import get_session
from src.presentation.schemas.auth_schema import (
    LoginRequestSchema,
    RefreshTokenRequestSchema,
    RegisterRequestSchema,
    TokenResponseSchema,
)
from src.presentation.schemas.common_schema import APIResponseSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponseSchema[dict],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequestSchema,
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[dict]:
    result = await container.register_user_use_case(session).execute(
        RegisterUserCommand(email=payload.email, password=payload.password)
    )
    await session.commit()
    return APIResponseSchema(data={"id": str(result.id), "email": result.email})


@router.post("/login", response_model=APIResponseSchema[TokenResponseSchema])
async def login(
    payload: LoginRequestSchema,
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TokenResponseSchema]:
    token = await container.login_use_case(session).execute(
        LoginCommand(email=payload.email, password=payload.password)
    )
    return APIResponseSchema(data=TokenResponseSchema(**asdict(token)))


@router.post("/refresh", response_model=APIResponseSchema[TokenResponseSchema])
async def refresh_token(
    payload: RefreshTokenRequestSchema,
    session: AsyncSession = Depends(get_session),
) -> APIResponseSchema[TokenResponseSchema]:
    token = await container.refresh_token_use_case(session).execute(
        RefreshTokenCommand(refresh_token=payload.refresh_token)
    )
    return APIResponseSchema(data=TokenResponseSchema(**asdict(token)))
