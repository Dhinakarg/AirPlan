"""Pure ventilation window discovery, inversion detection, and exposure window algorithms."""

from collections.abc import Callable

from app.constants import (
    INVERSION_BLH_M,
    OPEN_WINDOW_MAX_PM25_UG_M3,
    STAGNATION_HOURS,
    STAGNATION_WIND_KMH,
)
from app.engine.models import HourlyAir, InversionResult, Window


def _find_sliding_window(
    air: list[HourlyAir],
    min_hours: int,
    is_better: Callable[[float, float], bool],
    init_val: float,
) -> tuple[int, float] | None:
    """Find contiguous sliding window minimizing or maximizing mean PM2.5."""
    if len(air) < min_hours:
        return None
    best_idx = 0
    best_val = init_val
    for i in range(len(air) - min_hours + 1):
        mean_val = sum(pt.pm25 for pt in air[i : i + min_hours]) / min_hours
        if is_better(mean_val, best_val):
            best_val = mean_val
            best_idx = i
    return best_idx, best_val


def find_ventilation_window(
    air: list[HourlyAir],
    min_hours: int = 2,
) -> Window | None:
    """Identify the optimal contiguous window for natural window airing."""
    res = _find_sliding_window(air, min_hours, lambda a, b: a < b, float("inf"))
    if res is None:
        return None
    best_start, best_mean = res
    if best_mean > OPEN_WINDOW_MAX_PM25_UG_M3:
        return None
    selected = air[best_start : best_start + min_hours]
    return Window(
        start_hour=selected[0].hour,
        end_hour=selected[-1].hour + 1,
        mean_pm25=round(best_mean, 1),
        reason="Optimal low-PM2.5 interval for natural ventilation",
    )


def _flag_by_blh(air: list[HourlyAir]) -> list[int]:
    """Flag hours where boundary layer height drops below inversion threshold."""
    return [
        pt.hour
        for pt in air
        if pt.boundary_layer_m is not None and pt.boundary_layer_m < INVERSION_BLH_M
    ]


def _flag_by_stagnation(air: list[HourlyAir]) -> list[int]:
    """Flag nocturnal hours with stagnant surface wind speeds."""
    return [
        pt.hour for pt in air if pt.hour in STAGNATION_HOURS and pt.wind_kmh < STAGNATION_WIND_KMH
    ]


def detect_inversion(air: list[HourlyAir]) -> InversionResult:
    """Diagnose temperature inversion and stagnant air trap hours."""
    if any(pt.boundary_layer_m is not None for pt in air):
        return InversionResult(hours=_flag_by_blh(air), method="boundary_layer_height")
    return InversionResult(hours=_flag_by_stagnation(air), method="stagnation_proxy")


def worst_exposure_window(
    air: list[HourlyAir],
    min_hours: int = 2,
) -> Window | None:
    """Identify the contiguous time window with the highest average PM2.5."""
    res = _find_sliding_window(air, min_hours, lambda a, b: a > b, -1.0)
    if res is None:
        return None
    worst_start, worst_mean = res
    selected = air[worst_start : worst_start + min_hours]
    return Window(
        start_hour=selected[0].hour,
        end_hour=selected[-1].hour + 1,
        mean_pm25=round(worst_mean, 1),
        reason="Peak ambient smog window; keep windows sealed",
    )
