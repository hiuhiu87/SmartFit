from fastapi import FastAPI

from src.presentation.api.router import api_router
from src.presentation.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="SmartFit Backend", version="0.1.0")

    @app.get("/healthz", tags=["infra"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    register_exception_handlers(app)
    return app


app = create_app()
