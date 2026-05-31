import asyncio

from src.infrastructure.database.base import import_models, metadata
from src.infrastructure.database.session import engine


async def create_all_tables() -> None:
    import_models()
    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)


async def main() -> None:
    await create_all_tables()
    print("Database bootstrap completed: created tables from SQLModel metadata")


if __name__ == "__main__":
    asyncio.run(main())
