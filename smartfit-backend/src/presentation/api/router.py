from fastapi import APIRouter

from src.presentation.api.v1.ai_router import router as ai_router
from src.presentation.api.v1.auth_router import router as auth_router
from src.presentation.api.v1.exercise_router import router as exercise_router
from src.presentation.api.v1.health_router import router as health_router
from src.presentation.api.v1.progress_router import router as progress_router
from src.presentation.api.v1.readiness_router import router as readiness_router
from src.presentation.api.v1.user_router import router as user_router
from src.presentation.api.v1.workout_router import router as workout_router

api_router = APIRouter(prefix="/api")
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router)
v1_router.include_router(user_router)
v1_router.include_router(health_router)
v1_router.include_router(readiness_router)
v1_router.include_router(exercise_router)
v1_router.include_router(workout_router)
v1_router.include_router(ai_router)
v1_router.include_router(progress_router)
api_router.include_router(v1_router)
