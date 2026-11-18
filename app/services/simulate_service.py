"""Indoor aerosol dynamics and ventilation simulation service."""

from app.data.air_client import fetch_hourly_air
from app.engine.exposure import compare_routines
from app.engine.models import (
    AgeGroup,
    HomeProfile,
    HourlyAir,
    RoutineBlock,
    RoutineComparison,
)


def run_simulation(
    base_routine: list[RoutineBlock],
    alt_routine: list[RoutineBlock],
    home: HomeProfile,
    *,
    age_group: AgeGroup = AgeGroup.ADULT,
    air: list[HourlyAir] | None = None,
    latitude: float = 28.61,
    longitude: float = 77.21,
    date: str | None = None,
) -> RoutineComparison:
    """Compare baseline routine against an optimized alternative routine."""
    air_records = air if air is not None else fetch_hourly_air(latitude, longitude, date)
    return compare_routines(base_routine, alt_routine, air_records, home, age_group)
