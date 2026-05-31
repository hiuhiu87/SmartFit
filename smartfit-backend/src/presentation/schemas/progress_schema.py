from pydantic import BaseModel, Field


class ProgressOverviewResponseSchema(BaseModel):
    completed_workouts: int = 0
    average_readiness: float = 0.0


class PersonalRecordSchema(BaseModel):
    exercise: str
    value: float = Field(ge=0)
    unit: str


class PersonalRecordsResponseSchema(BaseModel):
    records: list[PersonalRecordSchema] = Field(default_factory=list)
