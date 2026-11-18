"""Test configuration and shared fixtures for AirLedger."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient instance for API smoke testing."""
    return TestClient(app)
