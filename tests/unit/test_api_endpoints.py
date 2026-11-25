"""API functional tests for health, plan, simulation, and home analyze endpoints."""

from http import HTTPStatus
from typing import Any

from starlette.testclient import TestClient

from app.api.schemas import ErrorEnvelope
from tests.conftest import get_canonical_routine_dicts

_valid_routine_blocks = get_canonical_routine_dicts


def test_health_endpoints(client: TestClient) -> None:
    """Verify healthcheck endpoints at /health, /api/health, and /api/v1/health."""
    for path in ("/health", "/api/health", "/api/v1/health"):
        res = client.get(path)
        assert res.status_code == HTTPStatus.OK
        assert res.json()["status"] == "ok"


def test_plan_endpoint_happy_path(
    client: TestClient,
    valid_plan_payload: dict[str, Any],
) -> None:
    """Verify POST /api/v1/plan produces valid day exposure plan and guidance."""
    response = client.post("/api/v1/plan", json=valid_plan_payload)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "Dhinakar" in data["members_exposure"]
    assert data["data_source"] in ("sample", "open-meteo")
    assert "ai_guidance" in data
    assert "summary" in data["ai_guidance"]
    assert "ranked_interventions" in data
    assert len(data["ranked_interventions"]) > 0
    assert "provenance" in data


def test_plan_validation_max_members_exceeded(client: TestClient) -> None:
    """Verify plan rejection when household members exceed ceiling of 6."""
    members = [
        {
            "name": f"Member_{i}",
            "age_group": "adult",
            "sensitivity": "none",
            "routine": _valid_routine_blocks(),
        }
        for i in range(7)
    ]
    payload = {
        "members": members,
        "latitude": 28.61,
        "longitude": 77.21,
    }
    response = client.post("/api/v1/plan", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data
    assert "correlation_id" in data
    ErrorEnvelope.model_validate(data)


def test_plan_validation_max_blocks_exceeded(client: TestClient) -> None:
    """Verify plan rejection when a member routine exceeds 12 blocks."""
    blocks = [
        {"start_hour": i, "end_hour": i + 1, "activity": "rest", "mode": "home"} for i in range(13)
    ]
    payload = {
        "members": [
            {
                "name": "Overworked",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": blocks,
            }
        ],
        "latitude": 28.61,
        "longitude": 77.21,
    }
    response = client.post("/api/v1/plan", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data
    assert "correlation_id" in data


def test_plan_validation_invalid_hours(client: TestClient) -> None:
    """Verify rejection of invalid routine block hours (>24)."""
    payload = {
        "members": [
            {
                "name": "InvalidHours",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": [{"start_hour": 0, "end_hour": 25, "activity": "sleep", "mode": "home"}],
            }
        ],
        "latitude": 28.61,
        "longitude": 77.21,
    }
    response = client.post("/api/v1/plan", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data


def test_plan_validation_extra_fields_rejected(client: TestClient) -> None:
    """Verify schema enforcement: unknown/extra fields are rejected with 422."""
    payload = {
        "members": [
            {
                "name": "ExtraFieldMember",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": _valid_routine_blocks(),
            }
        ],
        "latitude": 28.61,
        "longitude": 77.21,
        "malicious_unrecognized_key": "some_payload",
    }
    response = client.post("/api/v1/plan", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data
    assert "correlation_id" in data


def test_plan_validation_invalid_lat_lon(client: TestClient) -> None:
    """Verify geographic bounds enforcement on latitude and longitude."""
    payload_bad_lat = {
        "members": [
            {
                "name": "BadLat",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": _valid_routine_blocks(),
            }
        ],
        "latitude": 95.0,  # invalid: > 90
        "longitude": 77.21,
    }
    res = client.post("/api/v1/plan", json=payload_bad_lat)
    assert res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data1 = res.json()
    assert "error" in data1
    assert "latitude" in data1["error"]
    assert "correlation_id" in data1

    payload_bad_lon = {
        "members": [
            {
                "name": "BadLon",
                "age_group": "adult",
                "sensitivity": "none",
                "routine": _valid_routine_blocks(),
            }
        ],
        "latitude": 28.61,
        "longitude": 200.0,  # invalid: > 180
    }
    res2 = client.post("/api/v1/plan", json=payload_bad_lon)
    assert res2.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data2 = res2.json()
    assert "error" in data2
    assert "longitude" in data2["error"]
    assert "correlation_id" in data2


def test_simulate_endpoint_happy_path(client: TestClient) -> None:
    """Verify POST /api/v1/simulate evaluates routine modification index."""
    base_routine = _valid_routine_blocks()
    alt_routine = [
        {"start_hour": 0, "end_hour": 7, "activity": "sleep", "mode": "home"},
        {"start_hour": 7, "end_hour": 8, "activity": "cook", "mode": "home"},
        {"start_hour": 8, "end_hour": 18, "activity": "exercise", "mode": "home"},
        {"start_hour": 18, "end_hour": 24, "activity": "sleep", "mode": "home"},
    ]
    payload = {
        "base_routine": base_routine,
        "alt_routine": alt_routine,
        "home": {"leakiness": "average", "purifier": False},
        "age_group": "adult",
        "latitude": 28.61,
        "longitude": 77.21,
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["index_before"] == 100.0
    assert "index_after" in data
    assert "dose_saved_ug" in data
    assert "per_block_delta" in data
    assert "provenance" in data


def test_simulate_validation_extra_fields(client: TestClient) -> None:
    """Verify simulation rejects unmapped extra fields."""
    payload = {
        "base_routine": _valid_routine_blocks(),
        "alt_routine": _valid_routine_blocks(),
        "extra_field": "disallowed",
    }
    response = client.post("/api/v1/simulate", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data
    assert "extra_field" in data["error"]
    assert "correlation_id" in data


def test_home_analyze_endpoint_happy_path(client: TestClient) -> None:
    """Verify POST /api/v1/home/analyze identifies indoor pollution emission sources."""
    payload = {
        "cooking_fuel": "biomass",
        "kitchen_exhaust": "none",
        "incense": True,
        "mosquito_coil": True,
        "smokers": True,
        "sweeping": "dry",
    }
    response = client.post("/api/v1/home/analyze", json=payload)
    assert response.status_code == HTTPStatus.OK
    findings = response.json()["findings"]
    assert len(findings) > 0
    for f in findings:
        assert f["status"] == "suspected"
        assert len(f["fixes"]) > 0


def test_home_analyze_with_measured_reading(client: TestClient) -> None:
    """Verify that measured status requires both reading presence and threshold breach."""
    payload = {
        "cooking_fuel": "biomass",
        "kitchen_exhaust": "none",
        "incense": True,
        "mosquito_coil": False,
        "smokers": False,
        "sweeping": "wet",
        "indoor_pm25_reading": 150.0,
    }
    response = client.post("/api/v1/home/analyze", json=payload)
    assert response.status_code == HTTPStatus.OK
    findings = response.json()["findings"]
    measured_findings = [f for f in findings if f["status"] == "measured"]
    assert len(measured_findings) > 0


def test_home_analyze_validation_extra_fields(client: TestClient) -> None:
    """Verify home analysis schema rejects extra fields."""
    payload = {
        "cooking_fuel": "lpg",
        "extra_sensor_id": "xyz-123",
    }
    response = client.post("/api/v1/home/analyze", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "error" in data
    assert "extra_sensor_id" in data["error"]
    assert "correlation_id" in data


def test_plan_endpoint_includes_worst_window_and_facts(
    client: TestClient,
    valid_plan_payload: dict[str, Any],
) -> None:
    """Verify plan endpoint provides worst_window and facts with worst_* fields."""
    response = client.post("/api/v1/plan", json=valid_plan_payload)
    data = response.json()
    assert response.status_code == HTTPStatus.OK
    assert "worst_window" in data
    assert {"summary", "tips", "answer"}.issubset(data.get("ai_guidance", {}))
