from datetime import date as date_type

from pydantic import BaseModel


class CalculateReadinessRequestSchema(BaseModel):
    date: date_type


class ReadinessResponseSchema(BaseModel):
    date: date_type
    score: float
    category: str
    recommendation: str
    confidence: float
    explanation: str
