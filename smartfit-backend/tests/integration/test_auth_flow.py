from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from src.infrastructure.database.base import import_models, metadata
from src.infrastructure.database.models.health_model import (
    HealthSummaryModel,
    ManualCheckinModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
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
        import_models()
        await connection.run_sync(metadata.create_all)

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


@pytest.mark.asyncio
async def test_save_health_summary(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "health.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "health.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        response = await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "sleep_hours": 7.5,
                "sleep_efficiency": 89,
                "resting_heart_rate": 56,
                "heart_rate_variability": 62,
                "steps": 9100,
                "active_energy_kcal": 520,
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["date"] == "2026-05-31"
    assert payload["sleep_hours"] == 7.5
    assert payload["steps"] == 9100


@pytest.mark.asyncio
async def test_update_same_date_health_summary(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "health.update@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "health.update@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "sleep_hours": 6.5,
                "sleep_efficiency": 82,
                "resting_heart_rate": 60,
                "heart_rate_variability": 50,
                "steps": 7000,
                "active_energy_kcal": 430,
            },
        )
        response = await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "sleep_hours": 8.0,
                "sleep_efficiency": 91,
                "resting_heart_rate": 54,
                "heart_rate_variability": 68,
                "steps": 11000,
                "active_energy_kcal": 610,
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["sleep_hours"] == 8.0
    assert payload["resting_heart_rate"] == 54
    assert payload["steps"] == 11000


@pytest.mark.asyncio
async def test_save_manual_checkin(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "checkin.user@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "checkin.user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        response = await client.post(
            "/api/v1/health/manual-checkin",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "energy": 4,
                "soreness": 2,
                "stress": 2,
                "motivation": 5,
                "sleep_quality": 4,
                "notes": "Feeling good",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["energy"] == 4
    assert payload["notes"] == "Feeling good"


@pytest.mark.asyncio
async def test_update_same_date_manual_checkin(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "checkin.update@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "checkin.update@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/manual-checkin",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "energy": 2,
                "soreness": 4,
                "stress": 3,
                "motivation": 2,
                "sleep_quality": 2,
                "notes": "Tired",
            },
        )
        response = await client.post(
            "/api/v1/health/manual-checkin",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "energy": 5,
                "soreness": 1,
                "stress": 1,
                "motivation": 5,
                "sleep_quality": 5,
                "notes": "Recovered",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["energy"] == 5
    assert payload["soreness"] == 1
    assert payload["notes"] == "Recovered"


@pytest.mark.asyncio
async def test_latest_health_summary_returns_newest_record(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "health.latest@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "health.latest@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": "2026-05-30", "sleep_hours": 6.5, "steps": 8000},
        )
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": "2026-05-31", "sleep_hours": 7.9, "steps": 10500},
        )
        response = await client.get(
            "/api/v1/health/latest-summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["date"] == "2026-05-31"
    assert payload["sleep_hours"] == 7.9
    assert payload["steps"] == 10500


@pytest.mark.asyncio
async def test_calculate_readiness_from_health_summary(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "readiness.summary@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "readiness.summary@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-30",
                "resting_heart_rate": 58,
                "heart_rate_variability": 55,
            },
        )
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-29",
                "resting_heart_rate": 57,
                "heart_rate_variability": 57,
            },
        )
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "sleep_hours": 8.1,
                "resting_heart_rate": 55,
                "heart_rate_variability": 64,
                "steps": 9800,
            },
        )
        response = await client.post(
            "/api/v1/readiness/calculate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": "2026-05-31"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["date"] == "2026-05-31"
    assert payload["score"] > 0
    assert payload["confidence"] > 0


@pytest.mark.asyncio
async def test_calculate_readiness_from_manual_checkin(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "readiness.checkin@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "readiness.checkin@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/manual-checkin",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "energy": 5,
                "soreness": 1,
                "stress": 1,
                "motivation": 5,
                "sleep_quality": 5,
                "notes": "Ready to go",
            },
        )
        response = await client.post(
            "/api/v1/readiness/calculate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": "2026-05-31"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["score"] > 0
    assert payload["category"] in {
        "excellent",
        "good",
        "moderate",
        "low",
        "very_low",
    }


@pytest.mark.asyncio
async def test_calculate_readiness_with_missing_hrv_still_succeeds(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "readiness.nohrv@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "readiness.nohrv@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/summary",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": "2026-05-31",
                "sleep_hours": 7.2,
                "resting_heart_rate": 59,
                "steps": 8600,
            },
        )
        response = await client.post(
            "/api/v1/readiness/calculate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": "2026-05-31"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["score"] > 0
    assert payload["confidence"] > 0


@pytest.mark.asyncio
async def test_today_returns_existing_readiness(test_app) -> None:
    today = date.today().isoformat()
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "readiness.today@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "readiness.today@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        await client.post(
            "/api/v1/health/manual-checkin",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "date": today,
                "energy": 4,
                "soreness": 2,
                "stress": 2,
                "motivation": 4,
                "sleep_quality": 4,
            },
        )
        calculate_response = await client.post(
            "/api/v1/readiness/calculate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"date": today},
        )
        response = await client.get(
            "/api/v1/readiness/today",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert calculate_response.status_code == 200
    assert response.status_code == 200
    assert response.json()["data"]["date"] == calculate_response.json()["data"]["date"]
    assert (
        response.json()["data"]["score"] == calculate_response.json()["data"]["score"]
    )


@pytest.mark.asyncio
async def test_history_returns_multiple_records(test_app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "readiness.history@example.com", "password": "password123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "readiness.history@example.com", "password": "password123"},
        )
        access_token = login_response.json()["data"]["access_token"]
        for target_date, energy in [("2026-05-30", 3), ("2026-05-31", 5)]:
            await client.post(
                "/api/v1/health/manual-checkin",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "date": target_date,
                    "energy": energy,
                    "soreness": 2,
                    "stress": 2,
                    "motivation": 4,
                    "sleep_quality": 4,
                },
            )
            await client.post(
                "/api/v1/readiness/calculate",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"date": target_date},
            )
        response = await client.get(
            "/api/v1/readiness/history",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert len(payload) >= 2
    assert payload[0]["date"] >= payload[1]["date"]
