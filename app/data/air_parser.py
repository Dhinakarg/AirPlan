"""Open-Meteo response schemas and hourly payload normalization helpers."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.engine.models import HourlyAir
from app.errors import AirDataError


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


def safe_float(val: float | None, default: float) -> float:
    """Return converted float or default if None."""
    return float(val) if val is not None else default


def get_at(lst: list[float | None] | None, idx: int) -> float | None:
    """Safe indexed value retrieval from optional sequence."""
    return lst[idx] if lst and idx < len(lst) else None


def build_hourly_air(
    h: int,
    air_resp: OpenMeteoAirResponse,
    weather_resp: OpenMeteoWeatherResponse,
) -> HourlyAir:
    """Construct HourlyAir instance for a single hour from validated responses."""
    pm_val = get_at(air_resp.hourly.pm2_5, h)
    wind_val = get_at(weather_resp.hourly.wind_speed_10m, h)
    blh_val = get_at(weather_resp.hourly.boundary_layer_height, h)

    return HourlyAir(
        hour=h,
        pm25=safe_float(pm_val, 0.0),
        wind_kmh=safe_float(wind_val, 5.0),
        boundary_layer_m=float(blh_val) if blh_val is not None else None,
        source="live",
    )


def parse_and_zip(
    air_json: dict[str, object],
    weather_json: dict[str, object],
) -> list[HourlyAir]:
    """Validate API responses against Pydantic models and merge into HourlyAir sequence."""
    try:
        air_resp = OpenMeteoAirResponse.model_validate(air_json)
        weather_resp = OpenMeteoWeatherResponse.model_validate(weather_json)
    except ValidationError as err:
        raise AirDataError(f"Malformed air quality data payload: {err}") from err
    return [build_hourly_air(h, air_resp, weather_resp) for h in range(24)]
