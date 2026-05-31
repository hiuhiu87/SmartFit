from pydantic import BaseModel, Field


class AIChatRequestSchema(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AIChatResponseSchema(BaseModel):
    message: str
    provider: str = "stub"
