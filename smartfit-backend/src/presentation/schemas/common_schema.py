from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


class ErrorDetailSchema(BaseModel):
    code: str
    message: str


T = TypeVar("T")


class APIResponseSchema(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    data: T | None = None
    error: ErrorDetailSchema | None = None
