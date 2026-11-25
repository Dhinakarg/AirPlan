"""Pure deterministic commute mode comparison engine."""

from pydantic import BaseModel, ConfigDict, Field

from app.constants import BASELINE_EXPOSURE_INDEX, COMMUTE_MODE_FACTORS
from app.engine.commute_constants import (
    COMMUTE_BASE_FARE_INR,
    COMMUTE_CO2_KG_PER_KM,
    COMMUTE_COST_INR_PER_KM,
    COMMUTE_SPEED_KMH,
)
from app.engine.enums import Mode
from app.engine.models import ConfidenceLevel

COMMUTE_ASSUMPTIONS_TEXT: str = (
    "Assumes typical urban speed, standard NCR single-trip fares, grid/tailpipe "
    "CO2 emission factors per passenger-km, and microenvironment PM2.5 attenuation "
    "factors (walk/cycle=1.0, bus=0.9, metro=0.7, auto=1.3, car=0.6)."
)


class CommuteOption(BaseModel):
    """Single commute mode metrics for a household trip."""

    model_config = ConfigDict(frozen=True)

    mode: Mode = Field(description="Transit mode identifier")
    exposure_index: float = Field(ge=0.0, description="Relative PM2.5 exposure index")
    cost_inr: float = Field(ge=0.0, description="Estimated one-way trip cost in INR")
    duration_minutes: int = Field(ge=1, description="Estimated travel duration in minutes")
    co2_kg: float = Field(ge=0.0, description="Estimated trip CO2 emissions in kg")
    confidence: ConfidenceLevel = Field(default="low", description="Estimate confidence grade")


class CommuteComparison(BaseModel):
    """Comparison across all urban commute modes for a given distance."""

    model_config = ConfigDict(frozen=True)

    distance_km: float = Field(gt=0.0, description="One-way commute distance in km")
    ambient_pm25_ug_m3: float = Field(ge=0.0, description="Reference ambient PM2.5 (ug/m3)")
    confidence: ConfidenceLevel = Field(default="low", description="Overall confidence grade")
    assumptions: str = Field(description="Explicit modeling assumptions")
    options: list[CommuteOption] = Field(description="Per-mode comparison rows")


def compare_commute_modes(
    pm25_ug_m3: float,
    distance_km: float = 8.0,
) -> CommuteComparison:
    """Compare walk, cycle, metro, bus, auto-rickshaw, and car for a trip."""
    modes = (
        Mode.WALK,
        Mode.CYCLE,
        Mode.METRO,
        Mode.BUS,
        Mode.AUTO_RICKSHAW,
        Mode.CAR,
    )
    options: list[CommuteOption] = []
    for mode in modes:
        key = mode.value
        factor = COMMUTE_MODE_FACTORS[key]
        speed = COMMUTE_SPEED_KMH[key]
        cost = COMMUTE_BASE_FARE_INR[key] + COMMUTE_COST_INR_PER_KM[key] * distance_km
        co2 = COMMUTE_CO2_KG_PER_KM[key] * distance_km
        duration = max(1, round((distance_km / speed) * 60.0))
        options.append(
            CommuteOption(
                mode=mode,
                exposure_index=round(BASELINE_EXPOSURE_INDEX * factor, 1),
                cost_inr=round(cost, 1),
                duration_minutes=duration,
                co2_kg=round(co2, 2),
                confidence="low",
            )
        )
    return CommuteComparison(
        distance_km=round(distance_km, 1),
        ambient_pm25_ug_m3=round(pm25_ug_m3, 1),
        confidence="low",
        assumptions=COMMUTE_ASSUMPTIONS_TEXT,
        options=options,
    )
