"""Pure domain data models and value objects for exposure and ventilation modeling."""

from enum import StrEnum
from typing import Literal, NamedTuple, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class AgeGroup(StrEnum):
    """Demographic age categories determining physiological breathing rates."""

    TODDLER = "toddler"
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    SENIOR = "senior"


class Sensitivity(StrEnum):
    """Health susceptibility and vulnerability classifications."""

    NONE = "none"
    ASTHMA_OR_HEART = "asthma_or_heart"
    PREGNANT = "pregnant"


class Activity(StrEnum):
    """Physical activity categories determining minute ventilation rates."""

    SLEEP = "sleep"
    REST = "rest"
    LIGHT = "light"
    WALK = "walk"
    EXERCISE = "exercise"
    COOK = "cook"


class Mode(StrEnum):
    """Micro-environment and commute transit modes."""

    HOME = "home"
    WALK = "walk"
    CYCLE = "cycle"
    METRO = "metro"
    BUS = "bus"
    AUTO_RICKSHAW = "auto_rickshaw"
    CAR = "car"
    OUTDOOR = "outdoor"


class Leakiness(StrEnum):
    """Building envelope tightness classification."""

    TIGHT = "tight"
    AVERAGE = "average"
    LEAKY = "leaky"


class RoutineBlock(BaseModel):
    """Time-bounded activity and location block within a 24-hour daily routine."""

    model_config = ConfigDict(frozen=True)

    start_hour: int = Field(ge=0, le=23, description="Starting hour index (0-23)")
    end_hour: int = Field(ge=1, le=24, description="Ending hour index (1-24)")
    activity: Activity = Field(description="Activity being conducted")
    mode: Mode = Field(description="Micro-environment mode")


class HomeProfile(BaseModel):
    """Residential structure air infiltration characteristics and filtration status."""

    model_config = ConfigDict(frozen=True)

    leakiness: Leakiness = Field(
        default=Leakiness.AVERAGE,
        description="Building envelope tightness",
    )
    purifier: bool = Field(default=False, description="Active HEPA/Corsi-Rosenthal air cleaner")
    windows_open_hours: set[int] = Field(
        default_factory=set,
        description="Hours during which windows are actively open",
    )


class HourlyAir(BaseModel):
    """Ambient meteorological and air quality observations or forecast for a single hour."""

    model_config = ConfigDict(frozen=True)

    hour: int = Field(ge=0, le=23, description="Hour index (0-23)")
    pm25: float = Field(ge=0.0, description="Outdoor PM2.5 concentration in ug/m3")
    wind_kmh: float = Field(ge=0.0, description="Surface wind speed in km/h")
    boundary_layer_m: float | None = Field(
        default=None,
        ge=0.0,
        description="Atmospheric boundary layer height in meters, if available",
    )


ConfidenceLevel: TypeAlias = Literal["low", "medium", "high"]


class Provenance(BaseModel):
    """Documentation of calculation assumptions and scientific confidence ratings."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Underlying source formula or assumption explanation")
    confidence: ConfidenceLevel = Field(
        default="medium",
        description="Confidence grade",
    )


class HourExposure(BaseModel):
    """Calculated particulate matter exposure for a single hour."""

    model_config = ConfigDict(frozen=True)

    hour: int = Field(ge=0, le=23, description="Hour index (0-23)")
    pm25_ug_m3: float = Field(ge=0.0, description="Ambient PM2.5 at this hour (ug/m3)")
    microenvironment_factor: float = Field(ge=0.0, description="Effective attenuation/mode factor")
    breathing_rate_m3_per_h: float = Field(ge=0.0, description="Inhaled volume per hour (m3/h)")
    inhaled_dose_ug: float = Field(ge=0.0, description="Total inhaled PM2.5 particulate mass (ug)")
    mode: Mode = Field(description="Microenvironment mode")
    activity: Activity = Field(description="Activity type")
    provenance: Provenance = Field(description="Metadata assumptions")


class DayExposure(BaseModel):
    """Total 24-hour daily inhaled particulate dose and comparative exposure index."""

    model_config = ConfigDict(frozen=True)

    total_dose_ug: float = Field(ge=0.0, description="Summed 24-hour inhaled PM2.5 dose (ug)")
    index: float = Field(ge=0.0, description="Relative exposure index (baseline = 100.0)")
    hours: list[HourExposure] = Field(description="Hour-by-hour exposure points")
    provenance: Provenance = Field(description="Exposure estimation assumptions")


class BlockDelta(BaseModel):
    """Comparative dose delta for a single routine block."""

    model_config = ConfigDict(frozen=True)

    block: RoutineBlock = Field(description="Routine block")
    baseline_dose_ug: float = Field(ge=0.0, description="Baseline inhaled dose in ug")
    alt_dose_ug: float = Field(ge=0.0, description="Alternative routine inhaled dose in ug")
    dose_saved_ug: float = Field(description="Reduction in inhaled dose (ug)")


class RoutineComparison(BaseModel):
    """Comparative analysis between baseline and optimized alternative routines."""

    model_config = ConfigDict(frozen=True)

    index_before: float = Field(default=100.0, description="Baseline reference index")
    index_after: float = Field(ge=0.0, description="Alternative routine exposure index")
    dose_saved_ug: float = Field(description="Total absolute dose saved (ug)")
    per_block_delta: list[BlockDelta] = Field(description="Per-block breakdown of dose deltas")
    provenance: Provenance = Field(description="Comparison methodology assumptions")


class Window(BaseModel):
    """Contiguous time window recommendation for ventilation or hazard avoidance."""

    model_config = ConfigDict(frozen=True)

    start_hour: int = Field(ge=0, le=23, description="Starting hour index (0-23)")
    end_hour: int = Field(ge=1, le=24, description="Ending hour index (1-24)")
    mean_pm25: float = Field(
        ge=0.0,
        description="Average PM2.5 concentration across window (ug/m3)",
    )
    reason: str = Field(description="Actionable rationale for this window")


class InversionResult(NamedTuple):
    """Flagged temperature inversion hours and diagnostic method used."""

    hours: list[int]
    method: str
