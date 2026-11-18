"""Test configuration and shared fixtures for AirLedger."""

from typing import Any

import pytest
from starlette.testclient import TestClient

from app.api.middleware import reset_rate_limiter
from app.engine.models import (
    Activity,
    CookingFuel,
    HomeProfile,
    HomeSurvey,
    HourlyAir,
    KitchenExhaust,
    Leakiness,
    Mode,
    RoutineBlock,
    SweepingType,
)
from app.main import app


@pytest.fixture(autouse=True)
def clean_rate_limiter() -> None:
    """Reset rate limiter state before each test."""
    reset_rate_limiter()


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient instance for API smoke testing."""
    return TestClient(app)


@pytest.fixture
def sample_diurnal_air() -> list[HourlyAir]:
    """Generate a realistic 24-hour diurnal winter smog curve with BLH and wind."""
    # Peak smog morning/night, afternoon solar dip
    hourly_pm25 = [
        320.0,
        340.0,
        360.0,
        380.0,
        390.0,
        370.0,
        350.0,
        300.0,  # 00:00 - 07:00
        240.0,
        180.0,
        130.0,
        95.0,
        80.0,
        75.0,
        85.0,
        120.0,  # 08:00 - 15:00
        170.0,
        230.0,
        290.0,
        330.0,
        340.0,
        335.0,
        325.0,
        315.0,  # 16:00 - 23:00
    ]
    records: list[HourlyAir] = []
    for h in range(24):
        # Shallow boundary layer at night (<300m), deep in afternoon (>800m)
        blh = 180.0 if (h <= 7 or h >= 20) else 950.0
        wind = 4.0 if (h <= 7 or h >= 20) else 14.0
        records.append(
            HourlyAir(
                hour=h,
                pm25=hourly_pm25[h],
                wind_kmh=wind,
                boundary_layer_m=blh,
            )
        )
    return records


@pytest.fixture
def sample_stagnant_air_without_blh() -> list[HourlyAir]:
    """Generate 24-hour air data without boundary layer height (tests stagnation proxy)."""
    records: list[HourlyAir] = []
    for h in range(24):
        wind = 3.5 if (h <= 7 or h >= 20) else 12.0
        records.append(
            HourlyAir(
                hour=h,
                pm25=280.0,
                wind_kmh=wind,
                boundary_layer_m=None,
            )
        )
    return records


@pytest.fixture
def sample_home_profiles() -> dict[str, HomeProfile]:
    """Provide homes with tight, average, and leaky envelopes."""
    return {
        "tight_purifier": HomeProfile(leakiness=Leakiness.TIGHT, purifier=True),
        "tight_no_purifier": HomeProfile(leakiness=Leakiness.TIGHT, purifier=False),
        "average": HomeProfile(leakiness=Leakiness.AVERAGE, purifier=False),
        "leaky": HomeProfile(leakiness=Leakiness.LEAKY, purifier=False),
        "open_windows": HomeProfile(
            leakiness=Leakiness.AVERAGE,
            purifier=False,
            windows_open_hours={13, 14},
        ),
    }


@pytest.fixture
def sample_routine() -> list[RoutineBlock]:
    """Standard 24-hour daily baseline routine blocks."""
    return [
        RoutineBlock(start_hour=0, end_hour=7, activity=Activity.SLEEP, mode=Mode.HOME),
        RoutineBlock(start_hour=7, end_hour=8, activity=Activity.COOK, mode=Mode.HOME),
        RoutineBlock(start_hour=8, end_hour=9, activity=Activity.WALK, mode=Mode.WALK),
        RoutineBlock(start_hour=9, end_hour=17, activity=Activity.LIGHT, mode=Mode.HOME),
        RoutineBlock(start_hour=17, end_hour=18, activity=Activity.EXERCISE, mode=Mode.OUTDOOR),
        RoutineBlock(start_hour=18, end_hour=22, activity=Activity.REST, mode=Mode.HOME),
        RoutineBlock(start_hour=22, end_hour=24, activity=Activity.SLEEP, mode=Mode.HOME),
    ]


@pytest.fixture
def valid_routine_dicts() -> list[dict[str, Any]]:
    """Provide standard valid routine blocks in dictionary format."""
    return [
        {"start_hour": 0, "end_hour": 7, "activity": "sleep", "mode": "home"},
        {"start_hour": 7, "end_hour": 8, "activity": "cook", "mode": "home"},
        {"start_hour": 8, "end_hour": 18, "activity": "light", "mode": "home"},
        {"start_hour": 18, "end_hour": 24, "activity": "sleep", "mode": "home"},
    ]


@pytest.fixture
def valid_plan_payload(valid_routine_dicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Provide canonical valid payload for POST /api/v1/plan."""
    return {
        "members": [
            {
                "name": "Dhinakar",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": valid_routine_dicts,
            }
        ],
        "home": {
            "leakiness": "average",
            "purifier": False,
            "windows_open_hours": [13, 14],
        },
        "latitude": 28.61,
        "longitude": 77.21,
        "date": "2026-01-15",
        "budget_inr": 500.0,
        "language": "en",
    }


@pytest.fixture
def sample_home_survey() -> HomeSurvey:
    """Provide a standard baseline household survey with biomass and unvented kitchen."""
    return HomeSurvey(
        cooking_fuel=CookingFuel.WOOD,
        kitchen_exhaust=KitchenExhaust.NONE,
        incense=True,
        mosquito_coil=True,
        smokers=True,
        pets=False,
        sweeping=SweepingType.DRY,
        indoor_pm25_reading=None,
    )
