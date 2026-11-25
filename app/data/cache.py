"""In-memory TTLCache strategy for hourly air quality observations."""

from typing import Final

from cachetools import TTLCache

from app.engine.models import HourlyAir

AIR_CACHE_TTL_SECONDS: Final[int] = 900  # 15 minutes
AIR_CACHE_MAXSIZE: Final[int] = 256


class AirCache:
    """Bounded in-memory TTLCache container for hourly air quality observations."""

    def __init__(self, maxsize: int = AIR_CACHE_MAXSIZE, ttl: int = AIR_CACHE_TTL_SECONDS) -> None:
        """Initialize AirCache with capacity and expiration parameters."""
        self._cache: TTLCache[tuple[float, float, str], list[HourlyAir]] = TTLCache(
            maxsize=maxsize,
            ttl=ttl,
        )

    def get(self, lat: float, lon: float, date_str: str) -> list[HourlyAir] | None:
        """Retrieve cached observation if available."""
        key = make_cache_key(lat, lon, date_str)
        return self._cache.get(key)

    def set(self, lat: float, lon: float, date_str: str, data: list[HourlyAir]) -> None:
        """Insert or refresh cache entry."""
        key = make_cache_key(lat, lon, date_str)
        self._cache[key] = data

    def clear(self) -> None:
        """Purge all cached entries."""
        self._cache.clear()


_DEFAULT_AIR_CACHE = AirCache()


def make_cache_key(lat: float, lon: float, date_str: str) -> tuple[float, float, str]:
    """Generate normalized cache key with coordinates rounded to 2 decimal places."""
    return (round(lat, 2), round(lon, 2), date_str)


def get_cached_air(
    lat: float,
    lon: float,
    date_str: str,
    cache: AirCache | None = None,
) -> list[HourlyAir] | None:
    """Retrieve cached hourly air readings if not expired."""
    return (cache or _DEFAULT_AIR_CACHE).get(lat, lon, date_str)


def set_cached_air(
    lat: float,
    lon: float,
    date_str: str,
    data: list[HourlyAir],
    cache: AirCache | None = None,
) -> None:
    """Store hourly air readings in bounded in-memory cache."""
    (cache or _DEFAULT_AIR_CACHE).set(lat, lon, date_str, data)


def clear_air_cache(cache: AirCache | None = None) -> None:
    """Purge all entries from the air quality cache."""
    (cache or _DEFAULT_AIR_CACHE).clear()
