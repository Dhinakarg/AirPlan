"""Request and response Pydantic schemas for the API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.engine.models import (
    AgeGroup,
    CookingFuel,
    DayExposure,
    HomeProfile,
    HouseholdContext,
    InversionResult,
    KitchenExhaust,
    Provenance,
    RankedIntervention,
    RoutineBlock,
    Sensitivity,
    SourceFinding,
    SweepingType,
    Window,
)


class FamilyMemberInput(BaseModel):
    """Household individual member profile and daily schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=50, description="Family member identifier")
    age_group: AgeGroup = Field(default=AgeGroup.ADULT, description="Demographic age group")
    sensitivity: Sensitivity = Field(
        default=Sensitivity.NONE,
        description="Health vulnerability",
    )
    routine: list[RoutineBlock] = Field(
        min_length=1,
        max_length=12,
        description="Daily routine blocks (1-12 blocks)",
    )


class PlanRequest(BaseModel):
    """Comprehensive input payload for 24-hour clean-air planning."""

    model_config = ConfigDict(extra="forbid")

    members: list[FamilyMemberInput] = Field(
        min_length=1,
        max_length=6,
        description="Family members (max 6)",
    )
    home: HomeProfile = Field(default_factory=HomeProfile, description="Home envelope properties")
    latitude: float = Field(ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(ge=-180.0, le=180.0, description="Longitude coordinate")
    date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Optional date (YYYY-MM-DD)",
    )
    budget_inr: float = Field(
        default=500.0,
        ge=0.0,
        le=100000.0,
        description="Monthly clean-air budget ceiling in INR",
    )
    context: HouseholdContext | None = Field(
        default=None,
        description="Optional household context",
    )
    language: Literal["en", "hi"] = Field(
        default="en",
        description="UI and response language preference",
    )


class PlanResponse(BaseModel):
    """Orchestrated plan output with exposures, interventions, and AI guidance."""

    model_config = ConfigDict(extra="forbid")

    members_exposure: dict[str, DayExposure]
    ventilation_window: Window | None
    worst_window: Window | None
    inversion: InversionResult
    ranked_interventions: list[RankedIntervention]
    ai_guidance: dict[str, Any]
    data_source: str
    provenance: Provenance


class SimulateRequest(BaseModel):
    """Input payload for routine counterfactual simulation."""

    model_config = ConfigDict(extra="forbid")

    base_routine: list[RoutineBlock] = Field(
        min_length=1,
        max_length=12,
        description="Baseline routine blocks",
    )
    alt_routine: list[RoutineBlock] = Field(
        min_length=1,
        max_length=12,
        description="Alternative routine blocks",
    )
    home: HomeProfile = Field(default_factory=HomeProfile, description="Household structure")
    age_group: AgeGroup = Field(default=AgeGroup.ADULT, description="Subject age classification")
    latitude: float = Field(default=28.61, ge=-90.0, le=90.0, description="Latitude")
    longitude: float = Field(default=77.21, ge=-180.0, le=180.0, description="Longitude")
    date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Optional date",
    )


class HomeAnalyzeRequest(BaseModel):
    """Questionnaire evaluating domestic pollution emission sources."""

    model_config = ConfigDict(extra="forbid")

    cooking_fuel: CookingFuel = Field(
        default=CookingFuel.LPG,
        description="Primary cooking fuel",
    )
    kitchen_exhaust: KitchenExhaust = Field(
        default=KitchenExhaust.NONE,
        description="Kitchen exhaust status",
    )
    incense: bool = Field(default=False, description="Incense burning")
    mosquito_coil: bool = Field(default=False, description="Mosquito coil burning")
    smokers: bool = Field(default=False, description="Indoor smoking")
    pets: bool = Field(default=False, description="Domestic pets")
    sweeping: SweepingType = Field(default=SweepingType.DRY, description="Sweeping method")
    indoor_pm25_reading: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional indoor PM2.5 reading (ug/m3)",
    )


class HomeAnalyzeResponse(BaseModel):
    """Identified indoor pollution sources and prioritized mitigation measures."""

    model_config = ConfigDict(extra="forbid")

    findings: list[SourceFinding]


class PledgeRequest(BaseModel):
    """Community action pledge submission."""

    model_config = ConfigDict(extra="forbid")

    area_code: str = Field(
        pattern=r"^[A-Z0-9-]{3,10}$",
        description="Coarse geographic district code (e.g. DL-01)",
    )
    action: str = Field(min_length=2, max_length=50, description="Pledged action identifier")
    count: int = Field(default=1, ge=1, le=1000, description="Number of instances or days")


class PledgeResponse(BaseModel):
    """Pledge submission status confirmation."""

    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    area_code: str


class AskRequest(BaseModel):
    """User inquiry submission for AI assistant guidance."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=300, description="User question text")
    facts: dict[str, Any] = Field(default_factory=dict, description="Ground truth facts")
    language: Literal["en", "hi"] = Field(default="en", description="Target language")


class AskResponse(BaseModel):
    """Assistant guidance response with safe substituted placeholders."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    tips: list[str]
    answer: str
    is_red_flag: bool = Field(default=False, description="Whether inquiry triggered medical triage")
    red_flag: dict[str, Any] | None = Field(
        default=None,
        description="Optional clinical emergency triage details",
    )


class ErrorEnvelope(BaseModel):
    """Standardized error envelope returning error message and tracking id."""

    model_config = ConfigDict(extra="forbid")

    error: str
    correlation_id: str
