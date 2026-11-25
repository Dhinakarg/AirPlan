"""Atmospheric data ingestion client with local caching and offline fallback."""

import json
import logging
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import get_settings
from app.constants import (
    AIR_QUALITY_BASE_URL,
    HTTP_MAX_RETRIES,
    HTTP_TIMEOUT_SECONDS,
    WEATHER_FORECAST_BASE_URL,
)
from app.data.cache import get_cached_air, set_cached_air
from app.engine.models import HourlyAir
from app.errors import AirDataError

logger = logging.getLogger(__name__)


class OpenMeteoAirHourly(BaseModel):
    """Hourly PM2.5 readings from Open-Meteo Air Quality API."""

    model_config = ConfigDict(extra="ignore")
    pm2_5: list[float | None] = Field(description="Hourly PM2.5 concentrations")


class OpenMeteoAirResponse(BaseModel):
    """Container payload for Open-Meteo Air Quality response."""

    model_config = ConfigDict(extra="ignore")
    hourly: OpenMeteoAirHourly


class OpenMeteoWeatherHourly(BaseModel):
    """Hourly meteorological conditions from Open-Meteo Weather Forecast API."""

    model_config = ConfigDict(extra="ignore")
    wind_speed_10m: list[float | None] = Field(description="Hourly 10m wind speed in km/h")
    boundary_layer_height: list[float | None] | None = Field(
        default=None,
        description="Hourly boundary layer height in meters",
    )


class OpenMeteoWeatherResponse(BaseModel):
    """Container payload for Open-Meteo Weather response."""

    model_config = ConfigDict(extra="ignore")
    hourly: OpenMeteoWeatherHourly


def load_sample_air_data() -> list[HourlyAir]:
    """Load offline sample diurnal smog profile from bundled JSON dataset."""
    try:
        path = Path(__file__).parent / "sample_data.json"
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        return [
            HourlyAir(
                hour=int(item["hour"]),
                pm25=float(item["pm25"]),
                wind_kmh=float(item["wind_kmh"]),
                boundary_layer_m=item.get("boundary_layer_m"),
                source="sample",
            )
            for item in data.get("hourly", [])
        ]
    except Exception as exc:
        raise AirDataError(f"Failed loading sample smog dataset: {exc}") from exc


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
            logger.warning("Attempt %d failed requesting %s: %s", attempt, url, exc)
    raise last_err or AirDataError("Request failed after retries")


def _safe_float(val: float | None, default: float) -> float:
    """Return converted float or default if None."""
    return float(val) if val is not None else default


def _get_at(lst: list[float | None] | None, idx: int) -> float | None:
    """Safe indexed value retrieval from optional sequence."""
    return lst[idx] if lst and idx < len(lst) else None


def _build_hourly_air(
    h: int,
    air_resp: OpenMeteoAirResponse,
    weather_resp: OpenMeteoWeatherResponse,
) -> HourlyAir:
    """Construct HourlyAir instance for a single hour from validated responses."""
    pm_val = _get_at(air_resp.hourly.pm2_5, h)
    wind_val = _get_at(weather_resp.hourly.wind_speed_10m, h)
    blh_val = _get_at(weather_resp.hourly.boundary_layer_height, h)

    return HourlyAir(
        hour=h,
        pm25=_safe_float(pm_val, 0.0),
        wind_kmh=_safe_float(wind_val, 5.0),
        boundary_layer_m=float(blh_val) if blh_val is not None else None,
        source="live",
    )


def _parse_and_zip(
    air_json: dict[str, object],
    weather_json: dict[str, object],
) -> list[HourlyAir]:
    """Validate API responses against Pydantic models and merge into HourlyAir sequence."""
    try:
        air_resp = OpenMeteoAirResponse.model_validate(air_json)
        weather_resp = OpenMeteoWeatherResponse.model_validate(weather_json)
    except ValidationError as err:
        raise AirDataError(f"Malformed air quality data payload: {err}") from err
    return [_build_hourly_air(h, air_resp, weather_resp) for h in range(24)]


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
