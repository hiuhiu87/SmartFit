from dataclasses import dataclass, field


@dataclass(slots=True)
class ProgressOverviewDTO:
    completed_workouts: int = 0
    average_readiness: float = 0.0


@dataclass(slots=True)
class PersonalRecordsDTO:
    records: list[dict[str, str | float]] = field(default_factory=list)
