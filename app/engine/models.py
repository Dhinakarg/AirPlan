"""Pure domain data models and value objects for exposure and ventilation modeling."""

from typing import Literal, NamedTuple, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from app.engine.enums import (
    Activity,
    AgeGroup,
    CookingFuel,
    InterventionCategory,
    KitchenExhaust,
    Leakiness,
    Mode,
    Sensitivity,
    SweepingType,
)


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
    source: str = Field(default="live", description="Data provenance: 'live' or 'sample'")


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
    baseline_dose_ug: float = Field(ge=0.0, description="Dose without adjustment (ug)")
    alt_dose_ug: float = Field(ge=0.0, description="Dose with adjustment (ug)")
    dose_saved_ug: float = Field(description="Net particulate reduction (ug)")


class RoutineComparison(BaseModel):
    """Counterfactual comparison between baseline and optimized alternative routines."""

    model_config = ConfigDict(frozen=True)

    index_before: float = Field(ge=0.0, description="Baseline index (default 100.0)")
    index_after: float = Field(ge=0.0, description="Optimized routine index")
    dose_saved_ug: float = Field(description="Total micrograms saved")
    per_block_delta: list[BlockDelta] = Field(description="Dose changes per block")
    provenance: Provenance = Field(description="Modeling provenance")


class Window(BaseModel):
    """Contiguous time window identified for natural ventilation or peak exposure avoidance."""

    model_config = ConfigDict(frozen=True)

    start_hour: int = Field(ge=0, le=23, description="Starting hour index (0-23)")
    end_hour: int = Field(ge=1, le=24, description="Ending hour index (1-24)")
    mean_pm25: float = Field(ge=0.0, description="Window mean PM2.5 concentration in ug/m3")
    reason: str = Field(description="Domain rationale for window selection")


class InversionResult(NamedTuple):
    """Diagnosis of nocturnal temperature inversion and boundary layer stagnation."""

    hours: list[int]
    method: Literal["boundary_layer_height", "stagnation_proxy"]


class HomeSurvey(BaseModel):
    """Questionnaire evaluating domestic pollution emission sources."""

    model_config = ConfigDict(frozen=True)

    cooking_fuel: CookingFuel = Field(
        default=CookingFuel.LPG,
        description="Primary cooking fuel used in home",
    )
    kitchen_exhaust: KitchenExhaust = Field(
        default=KitchenExhaust.NONE,
        description="Exhaust status in kitchen",
    )
    incense: bool = Field(default=False, description="Routine agarbatti/dhoop burning")
    mosquito_coil: bool = Field(default=False, description="Use of smoldering mosquito coils")
    smokers: bool = Field(default=False, description="Tobacco smokers residing in home")
    pets: bool = Field(default=False, description="Domestic pets residing indoors")
    sweeping: SweepingType = Field(default=SweepingType.DRY, description="Flooring sweeping method")
    indoor_pm25_reading: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional indoor PM2.5 sensor reading in ug/m3",
    )


class SourceFinding(BaseModel):
    """Evaluated indoor combustion or aerosol emission source."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Identified indoor emission source")
    likelihood: float = Field(ge=0.0, le=1.0, description="Estimated presence likelihood (0-1)")
    evidence: str = Field(description="Observed habits or sensor evidence")
    status: Literal["suspected", "measured"] = Field(
        description="'measured' only when reading exceeds threshold, otherwise 'suspected'",
    )
    fixes: list[str] = Field(description="Actionable mitigation measures")


class Intervention(BaseModel):
    """Candidate behavioral, structural, or transit intervention."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Unique intervention identifier")
    title: str = Field(description="Human-readable title")
    category: InterventionCategory = Field(description="Intervention category")
    cost_inr_per_month: float = Field(ge=0.0, description="Estimated monthly cost in INR")
    effort: int = Field(ge=1, le=5, description="Subjective effort required (1=easy, 5=hard)")
    impact: float = Field(ge=0.0, le=1.0, description="Relative PM2.5 reduction impact (0-1)")
    feasibility_conditions: list[str] = Field(
        default_factory=list,
        description="Preconditions required (e.g., requires_home_ownership)",
    )
    rationale: str = Field(description="Scientific or practical reasoning")
    provenance: Provenance = Field(description="Assumption provenance and confidence")


class HouseholdContext(BaseModel):
    """Contextual household constraints and attributes for intervention ranking."""

    model_config = ConfigDict(frozen=True)

    owns_home: bool = Field(default=True, description="Whether family owns residence")
    has_transit_access: bool = Field(default=True, description="Access to metro/bus network")
    has_car: bool = Field(default=True, description="Private car ownership")
    has_smokers: bool = Field(default=False, description="Smokers present in home")
    has_asthma_or_heart: bool = Field(default=False, description="Vulnerable health members")
    has_children: bool = Field(default=False, description="Toddler or children present")
    cooking_fuel: CookingFuel = Field(default=CookingFuel.LPG, description="Cooking fuel")
    has_unvented_kitchen: bool = Field(default=False, description="Kitchen without vented exhaust")
    burns_incense_or_coils: bool = Field(default=False, description="Incense/mosquito coil use")


class RankedIntervention(BaseModel):
    """Intervention scored, constrained, and ranked for a specific household context."""

    model_config = ConfigDict(frozen=True)

    intervention: Intervention = Field(description="Target intervention")
    score: float = Field(ge=0.0, description="Cost-benefit ranking score")
    rank: int = Field(ge=1, description="Priority rank (1=top priority)")
    feasibility: float = Field(ge=0.0, le=1.0, description="Contextual feasibility multiplier")
    why_this_rank: str = Field(description="Plain-language justification for assigned rank")


class Pledge(BaseModel):
    """Coarse, privacy-safe community collective action pledge without PII."""

    model_config = ConfigDict(frozen=True)

    area_code: str = Field(description="Coarse geographic district code (e.g., DL-01)")
    action: str = Field(description="Action identifier (e.g., carpool, no_waste_burning)")
    count: int = Field(default=1, ge=1, description="Count of occurrences or days")


class CommunityImpact(BaseModel):
    """Aggregated environmental and emissions savings across community pledges."""

    model_config = ConfigDict(frozen=True)

    trips_avoided: int = Field(ge=0, description="Count of private vehicle trips avoided")
    km_avoided: float = Field(ge=0.0, description="Total passenger-km of vehicle travel avoided")
    co2_kg_avoided: float = Field(ge=0.0, description="Estimated tailpipe CO2 avoided in kg")
    participating_households: int = Field(ge=0, description="Count of contributing households")
    pm25_note: str = Field(description="Qualitative emission impact notice (never measured PM2.5)")


class RedFlag(BaseModel):
    """Severe medical symptom alert requiring immediate emergency care."""

    model_config = ConfigDict(frozen=True)

    symptom: str = Field(description="Detected alarming clinical symptom")
    urgency: Literal["immediate", "urgent"] = Field(description="Clinical urgency triage level")
    action: str = Field(description="Mandatory directive (overrides all planner advice)")
    language: Literal["en", "hi"] = Field(description="Detected language of query")


__all__ = [
    "Activity",
    "AgeGroup",
    "BlockDelta",
    "CommunityImpact",
    "ConfidenceLevel",
    "CookingFuel",
    "DayExposure",
    "HomeProfile",
    "HomeSurvey",
    "HourExposure",
    "HourlyAir",
    "HouseholdContext",
    "Intervention",
    "InterventionCategory",
    "InversionResult",
    "KitchenExhaust",
    "Leakiness",
    "Mode",
    "Pledge",
    "Provenance",
    "RankedIntervention",
    "RedFlag",
    "RoutineBlock",
    "RoutineComparison",
    "Sensitivity",
    "SourceFinding",
    "SweepingType",
    "Window",
]
