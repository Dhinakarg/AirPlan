"""Atmospheric data ingestion client with local caching and offline fallback."""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.constants import (
    AIR_QUALITY_BASE_URL,
    HTTP_MAX_RETRIES,
    HTTP_TIMEOUT_SECONDS,
    WEATHER_FORECAST_BASE_URL,
)
from app.context import get_correlation_id
from app.data.air_parser import (
    OpenMeteoAirHourly,
    OpenMeteoAirResponse,
    OpenMeteoWeatherHourly,
    OpenMeteoWeatherResponse,
)
from app.data.air_parser import (
    parse_and_zip as _parse_and_zip,
)
from app.data.cache import get_cached_air, set_cached_air
from app.engine.models import HourlyAir
from app.errors import AirDataError

__all__ = [
    "OpenMeteoAirHourly",
    "OpenMeteoAirResponse",
    "OpenMeteoWeatherHourly",
    "OpenMeteoWeatherResponse",
    "fetch_hourly_air",
    "load_sample_air_data",
    "load_scenario_air_data",
]

logger = logging.getLogger(__name__)


def _load_hourly_file(path: Path, source_tag: str) -> list[HourlyAir]:
    """Load hourly smog dataset from a bundled JSON file."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [
        HourlyAir(
            hour=int(item["hour"]),
            pm25=float(item["pm25"]),
            wind_kmh=float(item["wind_kmh"]),
            boundary_layer_m=item.get("boundary_layer_m"),
            source=source_tag,
        )
        for item in data.get("hourly", [])
    ]


def load_sample_air_data() -> list[HourlyAir]:
    """Load offline sample diurnal smog profile from bundled JSON dataset."""
    try:
        return _load_hourly_file(Path(__file__).parent / "sample_data.json", "sample")
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        raise AirDataError(f"Failed loading sample smog dataset: {exc}") from exc


def load_scenario_air_data(scenario: str) -> list[HourlyAir]:
    """Load bundled demo scenario ('severe', 'moderate', or 'cleaner')."""
    allowed = {"severe", "moderate", "cleaner"}
    if scenario not in allowed:
        raise AirDataError(f"Unknown air scenario: {scenario}")
    try:
        path = Path(__file__).parent / "scenarios" / f"{scenario}.json"
        return _load_hourly_file(path, f"demo:{scenario}")
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        raise AirDataError(f"Failed loading scenario '{scenario}': {exc}") from exc


def _request_with_retry(
    client: httpx.Client,
    url: str,
    params: dict[str, Any],
) -> httpx.Response:
    """Execute HTTP GET with bounded retries on transient transport failures."""
    last_err: Exception | None = None
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            resp = client.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_err = exc
            logger.warning(
                "Attempt %d failed requesting %s [correlation_id=%s]: %s",
                attempt,
                url,
                get_correlation_id(),
                exc,
            )
    raise last_err or AirDataError("Request failed after retries")


def _fetch_remote_air(http: httpx.Client, r_lat: float, r_lon: float) -> list[HourlyAir]:
    """Fetch live atmospheric data from Open-Meteo endpoints and parse into records."""
    air_res = _request_with_retry(
        http, AIR_QUALITY_BASE_URL, {"latitude": r_lat, "longitude": r_lon, "hourly": "pm2_5"}
    )
    weather_res = _request_with_retry(
        http,
        WEATHER_FORECAST_BASE_URL,
        {
            "latitude": r_lat,
            "longitude": r_lon,
            "hourly": "wind_speed_10m,boundary_layer_height",
            "wind_speed_unit": "kmh",
        },
    )
    return _parse_and_zip(air_res.json(), weather_res.json())


def _try_fetch_remote(
    http: httpx.Client, r_lat: float, r_lon: float, date_key: str
) -> list[HourlyAir]:
    """Execute live fetch with fallback on transport or API exceptions."""
    try:
        records = _fetch_remote_air(http, r_lat, r_lon)
        set_cached_air(r_lat, r_lon, date_key, records)
        return records
    except AirDataError:
        raise
    except (
        httpx.HTTPError,
        httpx.NetworkError,
        httpx.TimeoutException,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as exc:
        logger.warning(
            "Live air fetch failed for (%.2f, %.2f): %s. Falling back to sample data.",
            r_lat,
            r_lon,
            exc,
        )
        return load_sample_air_data()


def _fetch_with_lifecycle(
    http: httpx.Client, r_lat: float, r_lon: float, date_key: str, *, should_close: bool
) -> list[HourlyAir]:
    """Execute remote retrieval ensuring owned client is cleaned up."""
    try:
        return _try_fetch_remote(http, r_lat, r_lon, date_key)
    finally:
        if should_close:
            http.close()


def fetch_hourly_air(
    lat: float,
    lon: float,
    date: str | None = None,
    client: httpx.Client | None = None,
) -> list[HourlyAir]:
    """Fetch 24-hour diurnal ambient air readings with caching and offline fallback."""
    r_lat, r_lon = round(lat, 2), round(lon, 2)
    date_key = date or "latest"

    cached = get_cached_air(r_lat, r_lon, date_key)
    if cached is not None:
        return cached

    if get_settings().air_data_mode == "sample":
        return load_sample_air_data()

    http = client if client is not None else httpx.Client()
    return _fetch_with_lifecycle(http, r_lat, r_lon, date_key, should_close=client is None)
