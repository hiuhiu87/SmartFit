from datetime import datetime, timezone

from sqlmodel import SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


metadata = SQLModel.metadata


def import_models() -> None:
    from src.infrastructure.database.models import (
        ai_model,
        exercise_model,
        health_model,
        readiness_model,
        subscription_model,
        user_model,
        workout_model,
    )  # noqa: F401
