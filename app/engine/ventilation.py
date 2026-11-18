"""Pure ventilation window discovery, inversion detection, and exposure window algorithms."""

from app.constants import (
    INVERSION_BLH_M,
    OPEN_WINDOW_MAX_PM25_UG_M3,
    STAGNATION_HOURS,
    STAGNATION_WIND_KMH,
)
from app.engine.models import HourlyAir, InversionResult, Window


def find_ventilation_window(
    air: list[HourlyAir],
    min_hours: int = 2,
) -> Window | None:
    """Identify the optimal contiguous window for natural window airing.

    Args:
        air: 24-hour sequence of air observations.
        min_hours: Minimum contiguous duration in hours.

    Returns:
        Window instance if air quality permits, or None if air is uniformly bad.
    """
    if len(air) < min_hours:
        return None
    if all(pt.pm25 > OPEN_WINDOW_MAX_PM25_UG_M3 for pt in air):
        return None

    best_start = 0
    best_mean = float("inf")

    for i in range(len(air) - min_hours + 1):
        window_slice = air[i : i + min_hours]
        mean_val = sum(pt.pm25 for pt in window_slice) / min_hours
        if mean_val < best_mean:
            best_mean = mean_val
            best_start = i

    if best_mean > OPEN_WINDOW_MAX_PM25_UG_M3:
        return None

    selected = air[best_start : best_start + min_hours]
    return Window(
        start_hour=selected[0].hour,
        end_hour=selected[-1].hour + 1,
        mean_pm25=round(best_mean, 1),
        reason="Optimal low-PM2.5 interval for natural ventilation",
    )


def detect_inversion(air: list[HourlyAir]) -> InversionResult:
    """Diagnose temperature inversion and stagnant air trap hours.

    Args:
        air: Sequence of ambient hourly air records.

    Returns:
        InversionResult containing flagged hours and method used.
    """
    has_blh = any(pt.boundary_layer_m is not None for pt in air)
    if has_blh:
        flagged = [
            pt.hour
            for pt in air
            if pt.boundary_layer_m is not None and pt.boundary_layer_m < INVERSION_BLH_M
        ]
        return InversionResult(hours=flagged, method="boundary_layer_height")

    flagged = [
        pt.hour for pt in air if pt.hour in STAGNATION_HOURS and pt.wind_kmh < STAGNATION_WIND_KMH
    ]
    return InversionResult(hours=flagged, method="stagnation_proxy")


def worst_exposure_window(
    air: list[HourlyAir],
    min_hours: int = 2,
) -> Window | None:
    """Identify the contiguous time window with the highest average PM2.5.

    Args:
        air: Sequence of ambient air observations.
        min_hours: Window duration in hours.

    Returns:
        Window representing peak smog exposure window, or None if insufficient data.
    """
    if len(air) < min_hours:
        return None

    worst_start = 0
    worst_mean = -1.0

    for i in range(len(air) - min_hours + 1):
        window_slice = air[i : i + min_hours]
        mean_val = sum(pt.pm25 for pt in window_slice) / min_hours
        if mean_val > worst_mean:
            worst_mean = mean_val
            worst_start = i

    selected = air[worst_start : worst_start + min_hours]
    return Window(
        start_hour=selected[0].hour,
        end_hour=selected[-1].hour + 1,
        mean_pm25=round(worst_mean, 1),
        reason="Peak ambient smog window; keep windows sealed",
    )
