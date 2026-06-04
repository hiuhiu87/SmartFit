from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from src.infrastructure.database.base import import_models, metadata
from src.infrastructure.database.session import engine


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


async def _bootstrap_if_empty() -> bool:
    import_models()
    table_names = await _get_table_names()
    user_tables = table_names - {"alembic_version"}
    if user_tables:
        return False

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)
    return True


async def main() -> None:
    bootstrapped = await _bootstrap_if_empty()
    alembic_cfg = _alembic_config()

    if bootstrapped:
        command.stamp(alembic_cfg, "head")
        print("Database bootstrap completed: created schema from metadata and stamped head")
        return

    command.upgrade(alembic_cfg, "head")
    print("Alembic upgrade completed")


if __name__ == "__main__":
    asyncio.run(main())
