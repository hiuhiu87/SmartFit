from dataclasses import dataclass
from datetime import date as date_type


@dataclass(frozen=True)
class DateRange:
    start_date: date_type
    end_date: date_type


@dataclass(frozen=True)
class ConfidenceLevel:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
