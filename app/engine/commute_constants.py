"""Named speed, fare, and CO2 emission constants for commute mode comparison."""

from typing import Final

# Average urban door-to-door speeds (km/h)
COMMUTE_SPEED_KMH: Final[dict[str, float]] = {
    "walk": 4.5,
    "cycle": 14.0,
    "metro": 32.0,
    "bus": 18.0,
    "auto_rickshaw": 20.0,
    "car": 24.0,
}

# Tailpipe / lifecycle CO2 emission factors (kg CO2 per passenger-km)
COMMUTE_CO2_KG_PER_KM: Final[dict[str, float]] = {
    "walk": 0.0,
    "cycle": 0.0,
    "metro": 0.04,
    "bus": 0.08,
    "auto_rickshaw": 0.11,
    "car": 0.18,
}

# Base fare per trip (INR)
COMMUTE_BASE_FARE_INR: Final[dict[str, float]] = {
    "walk": 0.0,
    "cycle": 0.0,
    "metro": 10.0,
    "bus": 10.0,
    "auto_rickshaw": 25.0,
    "car": 0.0,
}

# Marginal per-km operating / ticket cost (INR/km)
COMMUTE_COST_INR_PER_KM: Final[dict[str, float]] = {
    "walk": 0.0,
    "cycle": 0.0,
    "metro": 3.5,
    "bus": 2.0,
    "auto_rickshaw": 12.0,
    "car": 11.0,
}
