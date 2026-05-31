from dataclasses import dataclass
from datetime import date as date_type


@dataclass(slots=True)
class ReadinessDTO:
    date: date_type
    score: float
    category: str
    recommendation: str
    confidence: float
    explanation: str
