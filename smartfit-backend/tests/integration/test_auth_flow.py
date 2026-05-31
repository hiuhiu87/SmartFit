from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from src.infrastructure.database.models.user_model import (
    UserEquipmentModel,
    UserModel,
    UserProfileModel,
)
from src.infrastructure.database.session import get_session


@pytest_asyncio.fixture
async def test_app(tmp_path: Path):
    db_path = tmp_path / "auth_test.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", future=True, echo=False
    )
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: UserModel.metadata.create_all(
                sync_conn,
                tables=[
                    UserModel.__table__,
                    UserProfileModel.__table__,
                    UserEquipmentModel.__table__,
                ],
            )
        )

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    yield app

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def error_test_app():
    router = APIRouter()

    @router.get("/boom")
    async def boom() -> dict:
        raise RuntimeError("unexpected failure")

    app = create_app()
    app.include_router(router)
    yield app


@pytest.mark.asyncio
async def test_register_success(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "auth.user1@example.com", "password": "password123"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["email"] == "auth.user1@example.com"
    assert payload["data"]["id"]


@pytest.mark.asyncio
async def test_duplicate_email_fails(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        first = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup.user@example.com", "password": "password123"},
        )
        second = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup.user@example.com", "password": "password123"},
        )

    assert first.status_code == 201
    assert second.status_code == 400
    payload = second.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_login_success(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login.user@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login.user@example.com", "password": "password123"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["access_token"]
    assert payload["data"]["refresh_token"]
    assert payload["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrong.pass@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong.pass@example.com", "password": "not-the-right-one"},
        )

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_users_me_with_valid_token_succeeds(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "me.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "me.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["email"] == "me.user@example.com"
    assert payload["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_users_me_without_token_fails(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "refresh.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh.user@example.com", "password": "password123"},
        )
        refresh_token = login_response.json()["data"]["refresh_token"]
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["access_token"]
    assert payload["data"]["refresh_token"]


@pytest.mark.asyncio
async def test_update_profile(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "profile.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "profile.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        response = await client.put(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "full_name": "Profile User",
                "age": 31,
                "height_cm": 171.5,
                "weight_kg": 68.2,
                "training_level": "intermediate",
                "primary_goal": "strength",
                "injuries": ["knee soreness"],
                "notes": "Updated during onboarding",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["full_name"] == "Profile User"
    assert payload["data"]["injuries"] == ["knee soreness"]
    assert payload["data"]["training_level"] == "intermediate"


@pytest.mark.asyncio
async def test_update_equipment(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "equipment.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "equipment.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        response = await client.put(
            "/api/v1/users/me/equipment",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"equipment_types": ["dumbbell", "bench", "bodyweight"]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["equipment_types"] == ["dumbbell", "bench", "bodyweight"]


@pytest.mark.asyncio
async def test_users_me_returns_profile_and_equipment(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "onboarding.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "onboarding.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.put(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "full_name": "Onboarding User",
                "age": 28,
                "height_cm": 170,
                "weight_kg": 62,
                "training_level": "beginner",
                "primary_goal": "fat_loss",
                "injuries": [],
                "notes": "first setup",
            },
        )
        await client.put(
            "/api/v1/users/me/equipment",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"equipment_types": ["resistance_band", "bodyweight"]},
        )
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["email"] == "onboarding.user@example.com"
    assert payload["profile"]["full_name"] == "Onboarding User"
    assert payload["equipment_types"] == ["resistance_band", "bodyweight"]


@pytest.mark.asyncio
async def test_equipment_replacement_removes_old_equipment(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "replace.eq@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "replace.eq@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.put(
            "/api/v1/users/me/equipment",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"equipment_types": ["dumbbell", "bench"]},
        )
        await client.put(
            "/api/v1/users/me/equipment",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"equipment_types": ["bodyweight"]},
        )
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["equipment_types"] == ["bodyweight"]


@pytest.mark.asyncio
async def test_internal_server_error_is_handled(error_test_app) -> None:
    transport = ASGITransport(app=error_test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "internal_server_error"
