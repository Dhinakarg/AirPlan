"""Smoke test verifying all application packages and modules can be cleanly imported."""

import importlib
from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from app.errors import AirLedgerError, ValidationError

MODULES_TO_IMPORT = [
    "app",
    "app.config",
    "app.constants",
    "app.errors",
    "app.main",
    "app.api",
    "app.api.routes",
    "app.api.schemas",
    "app.api.middleware",
    "app.api.deps",
    "app.services",
    "app.services.plan_service",
    "app.services.simulate_service",
    "app.services.home_service",
    "app.services.community_service",
    "app.services.assistant_service",
    "app.engine",
    "app.engine.models",
    "app.engine.exposure",
    "app.engine.ventilation",
    "app.engine.indoor_sources",
    "app.engine.interventions",
    "app.engine.ranking",
    "app.engine.community",
    "app.engine.safety_rules",
    "app.data",
    "app.data.air_client",
    "app.data.cache",
    "app.ai",
    "app.ai.provider",
    "app.ai.prompts",
    "app.ai.fallback",
    "app.ai.validator",
    "app.ai.guards",
]


@pytest.mark.parametrize("module_name", MODULES_TO_IMPORT)
def test_import_all_packages(module_name: str) -> None:
    """Smoke test: verify every package and module imports cleanly."""
    mod = importlib.import_module(module_name)
    assert mod is not None


def test_healthcheck_endpoint(client: TestClient) -> None:
    """Smoke test: verify health check returns ok."""
    response = client.get("/api/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "ok"


def test_root_endpoint(client: TestClient) -> None:
    """Smoke test: verify root returns ok."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "ok"


def test_domain_error_instantiation() -> None:
    """Smoke test: verify domain error instances."""
    err = ValidationError("Invalid value", {"field": "fuel"})
    assert isinstance(err, AirLedgerError)
    assert err.message == "Invalid value"
    assert err.details["field"] == "fuel"
