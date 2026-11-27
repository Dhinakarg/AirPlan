"""Indoor aerosol dynamics and ventilation simulation service."""

from app.data.air_client import fetch_hourly_air
from app.engine.exposure import compare_routines
from app.engine.models import RoutineComparison
from app.services.service_models import SimulationParams


def run_simulation(params: SimulationParams) -> RoutineComparison:
    """Compare baseline routine against an optimized alternative routine."""
    air_records = (
        params.air
        if params.air is not None
        else fetch_hourly_air(params.latitude, params.longitude, params.date)
    )
    return compare_routines(
        params.base_routine,
        params.alt_routine,
        air_records,
        params.home,
        params.age_group,
    )
