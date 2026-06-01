from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/smartfit"
    )
    JWT_SECRET_KEY: str = Field(default="change-me")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    AI_PROVIDER: str = Field(default="gemini")
    OPENAI_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash-lite")
    GEMINI_TIMEOUT_SECONDS: int = Field(default=20)
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=1200)
    ENVIRONMENT: str = Field(default="local")


@lru_cache
def get_settings() -> Settings:
    return Settings()
