"""Domain constants, physical units, and regulatory thresholds for AirLedger.

All factors carry explicit physical units and documented provenance assumptions.
"""

from typing import Final

# --- Air Quality Regulatory Standards (Micrograms per cubic meter, ug/m3) ---
WHO_PM25_24H_GUIDELINE_UG_M3: Final[float] = 15.0
NAAQS_PM25_24H_LIMIT_UG_M3: Final[float] = 60.0
SEVERE_SMOG_THRESHOLD_UG_M3: Final[float] = 250.0

# --- Building Infiltration Factors by Leakiness (Dimensionless, 0 to 1) ---
# Unit: Dimensionless ratio of indoor-to-outdoor concentration without active filtration
# Provenance: Empirical envelope infiltration literature for residential housing
INFILTRATION_TIGHT: Final[float] = 0.35
INFILTRATION_AVERAGE: Final[float] = 0.60
INFILTRATION_LEAKY: Final[float] = 0.85

INFILTRATION_FACTORS: Final[dict[str, float]] = {
    "tight": INFILTRATION_TIGHT,
    "average": INFILTRATION_AVERAGE,
    "leaky": INFILTRATION_LEAKY,
}

# --- Indoor Air Purifier Attenuation Factor (Dimensionless multiplier) ---
# Unit: Dimensionless multiplier applied to indoor infiltrated particulate matter
# Provenance: CADR-based mass-balance steady-state reduction factor (approx. 70% reduction)
PURIFIER_FACTOR: Final[float] = 0.30

# --- Open Window Infiltration Factor (Dimensionless multiplier) ---
# Unit: Dimensionless multiplier when windows are actively open for natural ventilation
# Provenance: Near-complete outdoor ambient equilibrium during open-window periods
OPEN_WINDOW_FACTOR: Final[float] = 0.90

# --- Commute and Microenvironment Mode Factors ---
# Unit: Dimensionless exposure multiplier relative to ambient PM2.5 concentration
# Provenance: Field observational studies on urban transit microenvironments (confidence: low)
MODE_FACTOR_WALK: Final[float] = 1.0
MODE_FACTOR_CYCLE: Final[float] = 1.0
MODE_FACTOR_METRO: Final[float] = 0.7
MODE_FACTOR_BUS: Final[float] = 0.9
MODE_FACTOR_AUTO_RICKSHAW: Final[float] = 1.3
MODE_FACTOR_CAR: Final[float] = 0.6
MODE_FACTOR_OUTDOOR: Final[float] = 1.0

COMMUTE_MODE_FACTORS: Final[dict[str, float]] = {
    "walk": MODE_FACTOR_WALK,
    "cycle": MODE_FACTOR_CYCLE,
    "metro": MODE_FACTOR_METRO,
    "bus": MODE_FACTOR_BUS,
    "auto_rickshaw": MODE_FACTOR_AUTO_RICKSHAW,
    "car": MODE_FACTOR_CAR,
}

# --- Baseline Adult Breathing Rates by Activity (Cubic meters per hour, m3/h) ---
# Unit: m3/h (minute ventilation volume)
# Provenance: EPA Exposure Factors Handbook and physiological literature
BREATHING_RATE_ADULT_SLEEP_M3_H: Final[float] = 0.30
BREATHING_RATE_ADULT_REST_M3_H: Final[float] = 0.40
BREATHING_RATE_ADULT_LIGHT_M3_H: Final[float] = 0.60
BREATHING_RATE_ADULT_WALK_M3_H: Final[float] = 0.90
BREATHING_RATE_ADULT_COOK_M3_H: Final[float] = 0.70
BREATHING_RATE_ADULT_EXERCISE_M3_H: Final[float] = 1.80

ACTIVITY_BREATHING_RATES_ADULT: Final[dict[str, float]] = {
    "sleep": BREATHING_RATE_ADULT_SLEEP_M3_H,
    "rest": BREATHING_RATE_ADULT_REST_M3_H,
    "light": BREATHING_RATE_ADULT_LIGHT_M3_H,
    "walk": BREATHING_RATE_ADULT_WALK_M3_H,
    "cook": BREATHING_RATE_ADULT_COOK_M3_H,
    "exercise": BREATHING_RATE_ADULT_EXERCISE_M3_H,
}

# --- Age Group Breathing Rate Scaling Multipliers ---
# Unit: Dimensionless physiological scale multiplier relative to adult ventilation
# Provenance: Pediatric and geriatric lung capacity scaling factors
AGE_BREATHING_MULTIPLIER_TODDLER: Final[float] = 0.35
AGE_BREATHING_MULTIPLIER_CHILD: Final[float] = 0.55
AGE_BREATHING_MULTIPLIER_TEEN: Final[float] = 0.85
AGE_BREATHING_MULTIPLIER_ADULT: Final[float] = 1.00
AGE_BREATHING_MULTIPLIER_SENIOR: Final[float] = 0.90

AGE_GROUP_BREATHING_MULTIPLIERS: Final[dict[str, float]] = {
    "toddler": AGE_BREATHING_MULTIPLIER_TODDLER,
    "child": AGE_BREATHING_MULTIPLIER_CHILD,
    "teen": AGE_BREATHING_MULTIPLIER_TEEN,
    "adult": AGE_BREATHING_MULTIPLIER_ADULT,
    "senior": AGE_BREATHING_MULTIPLIER_SENIOR,
}

# --- Ventilation & Smog Inversion Thresholds ---
# Maximum ambient PM2.5 threshold permitted for natural window ventilation (ug/m3)
OPEN_WINDOW_MAX_PM25_UG_M3: Final[float] = 100.0

# Boundary layer height ceiling indicative of shallow temperature inversion (meters)
INVERSION_BLH_M: Final[float] = 300.0

# Wind speed stagnation threshold (km/h) for nocturnal stagnation proxy
STAGNATION_WIND_KMH: Final[float] = 6.0

# Nocturnal and early-morning hour set for stagnation proxy evaluation
STAGNATION_HOURS: Final[frozenset[int]] = frozenset({20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7})

# Baseline index reference level for comparison
BASELINE_EXPOSURE_INDEX: Final[float] = 100.0
