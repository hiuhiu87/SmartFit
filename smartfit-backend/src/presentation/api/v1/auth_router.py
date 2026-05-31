from dataclasses import asdict

from fastapi import APIRouter, status

from app.container import container
from src.application.auth.commands import LoginCommand, RegisterUserCommand
from src.presentation.schemas.auth_schema import LoginRequestSchema, RegisterRequestSchema, TokenResponseSchema
from src.presentation.schemas.common_schema import APIResponseSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=APIResponseSchema[dict], status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequestSchema) -> APIResponseSchema[dict]:
    result = await container.register_user_use_case().execute(RegisterUserCommand(email=payload.email, password=payload.password))
    return APIResponseSchema(data={"id": str(result.id), "email": result.email})


@router.post("/login", response_model=APIResponseSchema[TokenResponseSchema])
async def login(payload: LoginRequestSchema) -> APIResponseSchema[TokenResponseSchema]:
    token = await container.login_use_case().execute(LoginCommand(email=payload.email, password=payload.password))
    return APIResponseSchema(data=TokenResponseSchema(**asdict(token)))
