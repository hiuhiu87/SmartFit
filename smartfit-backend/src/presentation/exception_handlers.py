import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.settings import get_settings
from src.domain.common.exceptions import (
    AIConfigurationError,
    AIGenerationError,
    AIInvalidOutputError,
    AIProviderTimeoutError,
    AIRateLimitError,
    AIUsageLimitExceededError,
    AIUnsafeOutputError,
    DomainError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "validation_error", "message": str(exc)},
            },
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "not_found", "message": str(exc)},
            },
        )

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {"code": "unauthorized", "message": str(exc)},
            },
        )

    @app.exception_handler(AIRateLimitError)
    async def handle_ai_rate_limit(_: Request, exc: AIRateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {"code": "ai_rate_limit", "message": str(exc)},
            },
        )

    @app.exception_handler(AIUsageLimitExceededError)
    async def handle_ai_usage_limit(
        _: Request, exc: AIUsageLimitExceededError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {"code": "AI_LIMIT_REACHED", "message": str(exc)},
            },
        )

    @app.exception_handler(AIProviderTimeoutError)
    async def handle_ai_timeout(
        _: Request, exc: AIProviderTimeoutError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "error": {"code": "ai_timeout", "message": str(exc)},
            },
        )

    @app.exception_handler(AIConfigurationError)
    async def handle_ai_configuration(
        _: Request, exc: AIConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {"code": "ai_configuration_error", "message": str(exc)},
            },
        )

    @app.exception_handler(AIGenerationError)
    async def handle_ai_generation(_: Request, exc: AIGenerationError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {"code": "ai_generation_error", "message": str(exc)},
            },
        )

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": "domain_error", "message": str(exc)},
            },
        )

    @app.exception_handler(Exception)
    async def handle_internal_server_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        settings = get_settings()
        logger.exception(
            "Unhandled exception while processing %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )

        message = "Internal server error"
        if settings.ENVIRONMENT.lower() in {"local", "development", "dev"}:
            message = f"Internal server error: {exc}"

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": "internal_server_error", "message": message},
            },
        )
