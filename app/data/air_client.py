"""Client for fetching live and forecasted air quality readings from Open-Meteo."""

import json
import logging
from pathlib import Path
from typing import Final

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import get_settings
from app.data.cache import get_cached_air, set_cached_air
from app.engine.models import HourlyAir
from app.errors import AirDataError

logger = logging.getLogger(__name__)

AIR_QUALITY_BASE_URL: Final[str] = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_FORECAST_BASE_URL: Final[str] = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT_SECONDS: Final[float] = 5.0
MAX_RETRIES: Final[int] = 2


class OpenMeteoAirHourly(BaseModel):
    """Schema for Open-Meteo air quality hourly array."""

    model_config = ConfigDict(extra="ignore")

    pm2_5: list[float | None] = Field(description="Hourly PM2.5 concentrations")


class OpenMeteoAirResponse(BaseModel):
    """Schema for Open-Meteo air quality response body."""

    model_config = ConfigDict(extra="ignore")

    hourly: OpenMeteoAirHourly


class OpenMeteoWeatherHourly(BaseModel):
    """Schema for Open-Meteo weather forecast hourly array."""

    model_config = ConfigDict(extra="ignore")

    wind_speed_10m: list[float | None] = Field(description="Hourly 10m wind speed in km/h")
    boundary_layer_height: list[float | None] | None = Field(
        default=None,
        description="Hourly boundary layer height in meters",
    )


class OpenMeteoWeatherResponse(BaseModel):
    """Schema for Open-Meteo weather forecast response body."""

    model_config = ConfigDict(extra="ignore")

    hourly: OpenMeteoWeatherHourly


def load_sample_air_data() -> list[HourlyAir]:
    """Load offline sample diurnal smog profile from bundled JSON dataset.

    Returns:
        24-hour sequence of HourlyAir marked with source='sample'.
    """
    path = Path(__file__).parent / "sample_data.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    records: list[HourlyAir] = []
    for item in data.get("hourly", []):
        records.append(
            HourlyAir(
                hour=int(item["hour"]),
                pm25=float(item["pm25"]),
                wind_kmh=float(item["wind_kmh"]),
                boundary_layer_m=item.get("boundary_layer_m"),
                source="sample",
            )
        )
    return records


def _request_with_retry(
    client: httpx.Client,
    url: str,
    params: dict[str, str | float],
) -> httpx.Response:
    """Execute GET request with max 2 retries on transient connection issues."""
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_err = exc
            if attempt == MAX_RETRIES:
                break
    raise last_err or AirDataError("Request failed after retries")


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

    records: list[HourlyAir] = []
    for h in range(24):
        pm_val = air_resp.hourly.pm2_5[h] if h < len(air_resp.hourly.pm2_5) else None
        wind_val = (
            weather_resp.hourly.wind_speed_10m[h]
            if h < len(weather_resp.hourly.wind_speed_10m)
            else None
        )
        blh_list = weather_resp.hourly.boundary_layer_height
        blh_val = blh_list[h] if blh_list and h < len(blh_list) else None

        records.append(
            HourlyAir(
                hour=h,
                pm25=float(pm_val) if pm_val is not None else 0.0,
                wind_kmh=float(wind_val) if wind_val is not None else 5.0,
                boundary_layer_m=float(blh_val) if blh_val is not None else None,
                source="live",
            )
        )
    return records


def fetch_hourly_air(
    lat: float,
    lon: float,
    date: str | None = None,
    client: httpx.Client | None = None,
) -> list[HourlyAir]:
    """Fetch 24-hour diurnal ambient air readings with caching and offline fallback.

    Args:
        lat: Latitude coordinate (rounded to 2 decimal places).
        lon: Longitude coordinate (rounded to 2 decimal places).
        date: Optional ISO date string (YYYY-MM-DD).
        client: Optional pre-configured httpx.Client (useful for mocked testing).

    Returns:
        List of 24 HourlyAir records with source indicating 'live' or 'sample'.
    """
    r_lat = round(lat, 2)
    r_lon = round(lon, 2)
    date_key = date or "latest"

    cached = get_cached_air(r_lat, r_lon, date_key)
    if cached is not None:
        return cached

    settings = get_settings()
    if settings.air_data_mode == "sample":
        return load_sample_air_data()

    http = client or httpx.Client()
    try:
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
        records = _parse_and_zip(air_res.json(), weather_res.json())
        set_cached_air(r_lat, r_lon, date_key, records)
        return records
    except AirDataError:
        raise
    except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError, Exception) as exc:
        logger.warning(
            "Live air fetch failed for (%.2f, %.2f): %s. Falling back to sample data.",
            r_lat,
            r_lon,
            exc,
        )
        return load_sample_air_data()
    finally:
        if client is None:
            http.close()
