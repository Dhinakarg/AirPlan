"""Unit tests for Open-Meteo air data client, caching, and offline fallback."""

import json
from collections.abc import Generator

import httpx
import pytest

from app.config import Settings
from app.data.air_client import (
    fetch_hourly_air,
    load_sample_air_data,
)
from app.data.cache import clear_air_cache, get_cached_air
from app.errors import AirDataError


@pytest.fixture(autouse=True)
def _reset_cache() -> Generator[None, None, None]:
    """Clear in-memory TTLCache before and after each test."""
    clear_air_cache()
    yield
    clear_air_cache()


@pytest.fixture(autouse=True)
def _set_live_mode_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default air_data_mode to 'live' for air client tests."""
    monkeypatch.setattr(
        "app.data.air_client.get_settings",
        lambda: Settings(air_data_mode="live"),
    )


def test_sample_data_loader_structure() -> None:
    """Bundled sample data loads 24 valid hourly records with source='sample'."""
    records = load_sample_air_data()
    assert len(records) == 24
    for h, rec in enumerate(records):
        assert rec.hour == h
        assert rec.pm25 >= 0.0
        assert rec.wind_kmh >= 0.0
        assert rec.source == "sample"


def test_coordinates_rounded_to_two_decimals() -> None:
    """Outbound coordinates are strictly rounded to 2 decimal places (privacy guard)."""
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        body = json.dumps({"hourly": {"pm2_5": [50.0] * 24, "wind_speed_10m": [5.0] * 24}})
        return httpx.Response(200, content=body)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetch_hourly_air(28.613912, 77.209021, client=client)

    assert captured_params.get("latitude") == "28.61"
    assert captured_params.get("longitude") == "77.21"


def test_successful_live_fetch_caches_result() -> None:
    """Successful live Open-Meteo responses merge into HourlyAir with source='live'."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        url_str = str(request.url)
        if "air-quality" in url_str:
            return httpx.Response(200, json={"hourly": {"pm2_5": [150.0] * 24}})
        return httpx.Response(
            200,
            json={"hourly": {"wind_speed_10m": [8.0] * 24, "boundary_layer_height": [400.0] * 24}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = fetch_hourly_air(28.61, 77.21, client=client)

    assert len(records) == 24
    assert records[0].source == "live"
    assert records[0].pm25 == 150.0
    assert records[0].wind_kmh == 8.0
    assert records[0].boundary_layer_m == 400.0
    assert call_count == 2

    # Cache hit check
    cached = get_cached_air(28.61, 77.21, "latest")
    assert cached is not None


def test_cache_hit_avoids_second_network_call() -> None:
    """Cache hit retrieves cached records without making additional HTTP requests."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if "air-quality" in str(request.url):
            return httpx.Response(200, json={"hourly": {"pm2_5": [100.0] * 24}})
        return httpx.Response(200, json={"hourly": {"wind_speed_10m": [6.0] * 24}})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    # First call: makes 2 HTTP requests
    records_1 = fetch_hourly_air(28.61, 77.21, client=client)
    assert call_count == 2

    # Second call: served from cache, zero network calls
    records_2 = fetch_hourly_air(28.61, 77.21, client=client)
    assert call_count == 2
    assert records_1 == records_2


def test_timeout_falls_back_to_sample_data() -> None:
    """Network timeout during live fetch transparently returns sample data."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = fetch_hourly_air(28.61, 77.21, client=client)

    assert len(records) == 24
    assert records[0].source == "sample"


def test_network_error_falls_back_to_sample_data() -> None:
    """Connection failure during live fetch transparently returns sample data."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("DNS resolution failed", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = fetch_hourly_air(28.61, 77.21, client=client)

    assert len(records) == 24
    assert records[0].source == "sample"


def test_air_data_mode_sample_skips_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """AIR_DATA_MODE=sample configuration bypasses all external network calls."""
    monkeypatch.setattr(
        "app.data.air_client.get_settings",
        lambda: Settings(air_data_mode="sample"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Network must not be reached in sample mode")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = fetch_hourly_air(28.61, 77.21, client=client)
    assert len(records) == 24
    assert records[0].source == "sample"


def test_malformed_payload_raises_air_data_error() -> None:
    """Invalid JSON payload missing required hourly fields raises custom AirDataError."""

    def handler(request: httpx.Request) -> httpx.Response:
        # Returns 200 OK but invalid payload missing 'pm2_5'
        return httpx.Response(200, json={"unexpected_format": "bad_data"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AirDataError, match="Malformed air quality data payload"):
        fetch_hourly_air(28.61, 77.21, client=client)
