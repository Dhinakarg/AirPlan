"""In-memory TTLCache strategy for hourly air quality observations."""

from typing import Final

from cachetools import TTLCache

from app.engine.models import HourlyAir

AIR_CACHE_TTL_SECONDS: Final[int] = 900  # 15 minutes
AIR_CACHE_MAXSIZE: Final[int] = 256

_AIR_CACHE: TTLCache[tuple[float, float, str], list[HourlyAir]] = TTLCache(
    maxsize=AIR_CACHE_MAXSIZE,
    ttl=AIR_CACHE_TTL_SECONDS,
)


def make_cache_key(lat: float, lon: float, date_str: str) -> tuple[float, float, str]:
    """Generate normalized cache key with coordinates rounded to 2 decimal places."""
    return (round(lat, 2), round(lon, 2), date_str)


def get_cached_air(lat: float, lon: float, date_str: str) -> list[HourlyAir] | None:
    """Retrieve cached hourly air readings if not expired.

    Args:
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        date_str: ISO date string (YYYY-MM-DD).

    Returns:
        Cached list of HourlyAir, or None if not found or expired.
    """
    key = make_cache_key(lat, lon, date_str)
    return _AIR_CACHE.get(key)


def set_cached_air(
    lat: float,
    lon: float,
    date_str: str,
    data: list[HourlyAir],
) -> None:
    """Store hourly air readings in bounded in-memory cache.

    Args:
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        date_str: ISO date string (YYYY-MM-DD).
        data: List of HourlyAir records to cache.
    """
    key = make_cache_key(lat, lon, date_str)
    _AIR_CACHE[key] = data


def clear_air_cache() -> None:
    """Purge all entries from the air quality cache."""
    _AIR_CACHE.clear()
