from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from src.infrastructure.database.models.exercise_model import (
    ExerciseAlternativeModel,
    ExerciseModel,
)
from src.infrastructure.database.session import get_session
from src.infrastructure.seed.seed_exercises import _seed_rows


@pytest_asyncio.fixture
async def exercise_test_app(tmp_path: Path):
    db_path = tmp_path / "exercise_test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", future=True, echo=False
    )
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: ExerciseModel.metadata.create_all(
                sync_conn,
                tables=[
                    ExerciseModel.__table__,
                    ExerciseAlternativeModel.__table__,
                ],
            )
        )

    async with session_factory() as session:
        session.add_all(_seed_rows())
        await session.commit()

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    yield app

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_list_exercises_returns_seeded_exercises(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/exercises")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] >= 5
    assert len(payload["items"]) >= 5


@pytest.mark.asyncio
async def test_list_exercises_filter_by_primary_muscle(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/api/v1/exercises", params={"primary_muscle": "chest"}
        )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items
    assert all(item["primary_muscle"] == "chest" for item in items)


@pytest.mark.asyncio
async def test_list_exercises_filter_by_equipment(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/api/v1/exercises", params={"equipment": "dumbbell"}
        )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items
    assert all(item["equipment"] == "dumbbell" for item in items)


@pytest.mark.asyncio
async def test_list_exercises_filter_by_difficulty(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/api/v1/exercises", params={"difficulty": "beginner"}
        )

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items
    assert all(item["difficulty"] == "beginner" for item in items)


@pytest.mark.asyncio
async def test_list_exercises_limit_offset(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        first_page = await client.get(
            "/api/v1/exercises", params={"limit": 2, "offset": 0}
        )
        second_page = await client.get(
            "/api/v1/exercises", params={"limit": 2, "offset": 2}
        )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    first_items = first_page.json()["data"]["items"]
    second_items = second_page.json()["data"]["items"]
    assert len(first_items) == 2
    assert len(second_items) >= 1
    assert first_items[0]["id"] != second_items[0]["id"]


@pytest.mark.asyncio
async def test_get_exercise_by_id_returns_detail(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        list_response = await client.get(
            "/api/v1/exercises", params={"equipment": "dumbbell"}
        )
        exercise_id = list_response.json()["data"]["items"][0]["id"]
        response = await client.get(f"/api/v1/exercises/{exercise_id}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == exercise_id
    assert payload["name"]
    assert "primary_muscle" in payload


@pytest.mark.asyncio
async def test_get_exercise_by_id_not_found(exercise_test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=exercise_test_app), base_url="http://testserver"
    ) as client:
        response = await client.get(f"/api/v1/exercises/{uuid4()}")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"
