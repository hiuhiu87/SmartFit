from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.common.exceptions import DomainError, NotFoundError, UnauthorizedError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"success": False, "error": {"code": "validation_error", "message": str(exc)}})

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"success": False, "error": {"code": "not_found", "message": str(exc)}})

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"success": False, "error": {"code": "unauthorized", "message": str(exc)}})

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"success": False, "error": {"code": "domain_error", "message": str(exc)}})
