"""Immutable service parameter dataclasses avoiding wide function signatures."""

from dataclasses import dataclass
from typing import Any

from app.ai.provider import AssistantProvider
from app.engine.commute import CommuteComparison
from app.engine.enums import AgeGroup
from app.engine.models import (
    DayExposure,
    HomeProfile,
    HourlyAir,
    HouseholdContext,
    InversionResult,
    RankedIntervention,
    RoutineBlock,
    Window,
)


@dataclass(frozen=True)
class PlanBuildData:
    """Computed domain outputs assembled into a PlanResponse."""

    members_exp: dict[str, DayExposure]
    air: list[HourlyAir]
    vent_win: Window | None
    worst_win: Window | None
    inversion: InversionResult
    ranked: list[RankedIntervention]
    commute_cmp: CommuteComparison
    guidance: dict[str, Any]


@dataclass(frozen=True)
class PlanRequestParams:
    """Validated household and atmospheric parameters for clean-air planning."""

    members: list[Any]
    home: HomeProfile
    latitude: float
    longitude: float
    date: str | None = None
    budget_inr: float = 500.0
    context: HouseholdContext | None = None
    language: str = "en"
    provider: AssistantProvider | None = None
    scenario: str = "live"
    commute_distance_km: float = 8.0


@dataclass(frozen=True)
class SimulationParams:
    """Parameters for counterfactual routine exposure comparison."""

    base_routine: list[RoutineBlock]
    alt_routine: list[RoutineBlock]
    home: HomeProfile
    age_group: AgeGroup = AgeGroup.ADULT
    air: list[HourlyAir] | None = None
    latitude: float = 28.61
    longitude: float = 77.21
    date: str | None = None

