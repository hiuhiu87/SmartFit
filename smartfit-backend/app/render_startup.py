import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlmodel import func, select

from src.infrastructure.database.base import import_models, metadata
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.session import engine
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.seed.seed_exercises import seed_exercises


def _alembic_config() -> Config:
    project_root = Path(__file__).resolve().parents[1]
    return Config(str(project_root / "alembic.ini"))


async def _get_table_names() -> set[str]:
    async with engine.begin() as connection:
        return set(
            await connection.run_sync(
                lambda sync_connection: inspect(sync_connection).get_table_names()
            )
        )


async def _create_all_tables() -> None:
    import_models()

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)


async def _prepare_database() -> str:
    try:
        table_names = await _get_table_names()
        user_tables = table_names - {"alembic_version"}
        has_alembic_version = "alembic_version" in table_names

        if not user_tables:
            await _create_all_tables()
            return "bootstrap_and_stamp"

        if not has_alembic_version:
            await _create_all_tables()
            return "stamp_existing_schema"

        return "upgrade"
    finally:
        await engine.dispose()


async def _get_exercise_count() -> int:
    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(ExerciseModel)
        )
        return int(result.scalar_one())


async def _seed_exercises_if_empty() -> int:
    try:
        exercise_count = await _get_exercise_count()
        if exercise_count > 0:
            print(f"Exercise seed skipped: existing rows={exercise_count}")
            return 0

        inserted = await seed_exercises()
        print(f"Exercise seed completed during startup: inserted={inserted}")
        return inserted
    finally:
        await engine.dispose()


def main() -> None:
    action = asyncio.run(_prepare_database())
    alembic_cfg = _alembic_config()

    if action == "bootstrap_and_stamp":
        command.stamp(alembic_cfg, "head")
        print("Database bootstrap completed: created schema from metadata and stamped head")
        asyncio.run(_seed_exercises_if_empty())
        return

    if action == "stamp_existing_schema":
        command.stamp(alembic_cfg, "head")
        print("Existing schema detected without alembic_version: stamped head")
        asyncio.run(_seed_exercises_if_empty())
        return

    command.upgrade(alembic_cfg, "head")
    print("Alembic upgrade completed")
    asyncio.run(_seed_exercises_if_empty())


if __name__ == "__main__":
    main()
