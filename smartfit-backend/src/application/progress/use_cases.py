from src.application.progress.dto import PersonalRecordsDTO, ProgressOverviewDTO
from src.application.progress.queries import PersonalRecordsQuery, ProgressOverviewQuery


class GetProgressOverviewUseCase:
    async def execute(self, query: ProgressOverviewQuery) -> ProgressOverviewDTO:
        # TODO: aggregate workout history and readiness trend.
        return ProgressOverviewDTO()


class GetPersonalRecordsUseCase:
    async def execute(self, query: PersonalRecordsQuery) -> PersonalRecordsDTO:
        # TODO: compute personal records from workout logs.
        return PersonalRecordsDTO()
