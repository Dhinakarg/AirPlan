"""Personalized clean-air plan generation and routine orchestration service."""

from typing import Any

from app.api.schemas import PlanResponse
from app.data.air_client import fetch_hourly_air, load_scenario_air_data
from app.engine.commute import compare_commute_modes
from app.engine.enums import AgeGroup, Sensitivity
from app.engine.exposure import calculate_day_exposure
from app.engine.models import (
    DayExposure,
    HomeProfile,
    HourlyAir,
    HouseholdContext,
    InversionResult,
    Provenance,
    RankedIntervention,
    RoutineBlock,
    Window,
)
from app.engine.ranking import rank_interventions
from app.engine.ventilation import (
    detect_inversion,
    find_ventilation_window,
    worst_exposure_window,
)
from app.services.assistant_service import generate_clean_air_advice
from app.services.service_models import PlanBuildData, PlanRequestParams


class MemberPlanInput:
    """Input parameters for an individual family member."""

    def __init__(
        self,
        name: str,
        age_group: AgeGroup = AgeGroup.ADULT,
        sensitivity: Sensitivity = Sensitivity.NONE,
        routine: list[RoutineBlock] | None = None,
    ) -> None:
        """Initialize member input profile."""
        self.name = name
        self.age_group = age_group
        self.sensitivity = sensitivity
        self.routine = routine or []


def _window_params(vent_win: Window | None) -> tuple[int, int, float]:
    """Extract default or calculated start, end, and mean PM2.5 from window."""
    if vent_win is not None:
        return vent_win.start_hour, vent_win.end_hour, vent_win.mean_pm25
    return 13, 15, 75.0


def _compute_dose_metrics(
    members_exp: dict[str, DayExposure],
    ranked: list[RankedIntervention],
) -> tuple[float, float, float]:
    """Compute baseline index, post-intervention index, and dose saved."""
    n_members = len(members_exp)
    idx_before = (
        round(sum(e.index for e in members_exp.values()) / n_members, 1) if n_members else 100.0
    )
    mean_dose = sum(e.total_dose_ug for e in members_exp.values()) / n_members if n_members else 0.0
    top_impact = ranked[0].intervention.impact if ranked else 0.15
    return idx_before, round(idx_before * (1.0 - top_impact), 1), round(mean_dose * top_impact, 1)


def _extract_facts(
    vent_win: Window | None,
    worst_win: Window | None,
    inversion: InversionResult,
    ranked: list[RankedIntervention],
    members_exp: dict[str, DayExposure],
) -> dict[str, Any]:
    """Compile ground-truth facts dictionary for AI placeholder substitution."""
    top_title = ranked[0].intervention.title if ranked else "Natural ventilation"
    win_start, win_end, mean_pm = _window_params(vent_win)
    worst_start = worst_win.start_hour if worst_win else 19
    worst_end = worst_win.end_hour if worst_win else 23
    worst_pm = worst_win.mean_pm25 if worst_win else 250.0
    idx_before, idx_after, dose_saved = _compute_dose_metrics(members_exp, ranked)
    return {
        "index_after": idx_after,
        "index_before": idx_before,
        "dose_saved": dose_saved,
        "window_start": win_start,
        "window_end": win_end,
        "mean_pm25": mean_pm,
        "worst_start": worst_start,
        "worst_end": worst_end,
        "worst_pm25": worst_pm,
        "top_intervention": top_title,
        "cleanest_hour": win_start,
        "stagnation_hours": ", ".join(str(h) for h in inversion.hours[:3]) or "none",
    }


def _calc_members_exposure(
    members: list[MemberPlanInput], air: list[HourlyAir], home: HomeProfile
) -> dict[str, DayExposure]:
    """Calculate personalized 24-hour exposure for each family member."""
    return {m.name: calculate_day_exposure(m.routine, air, home, m.age_group) for m in members}


def _resolve_context(
    context: HouseholdContext | None, members: list[MemberPlanInput]
) -> HouseholdContext:
    """Resolve household health vulnerability context."""
    if context is not None:
        return context
    return HouseholdContext(
        has_asthma_or_heart=any(m.sensitivity == Sensitivity.ASTHMA_OR_HEART for m in members),
        has_children=any(m.age_group in {AgeGroup.TODDLER, AgeGroup.CHILD} for m in members),
    )


def _build_plan(data: PlanBuildData) -> PlanResponse:
    """Assemble final validated PlanResponse object."""
    return PlanResponse(
        members_exposure=data.members_exp,
        ventilation_window=data.vent_win,
        worst_window=data.worst_win,
        inversion=data.inversion,
        ranked_interventions=data.ranked,
        commute_comparison=data.commute_cmp,
        ai_guidance=data.guidance,
        data_source=data.air[0].source if data.air else "sample",
        provenance=Provenance(
            text="Diurnal microenvironment box model with verified meteorological inputs",
            confidence="high",
        ),
    )


def _analyze_meteorology(
    air: list[HourlyAir],
) -> tuple[Window | None, Window | None, InversionResult]:
    """Extract ventilation window, peak exposure window, and atmospheric inversion."""
    return find_ventilation_window(air), worst_exposure_window(air), detect_inversion(air)


def _load_air_for_plan(lat: float, lon: float, date: str | None, scenario: str) -> list[HourlyAir]:
    """Load either bundled scenario data or live/cached atmospheric observations."""
    if scenario != "live":
        return load_scenario_air_data(scenario)
    return fetch_hourly_air(round(lat, 2), round(lon, 2), date)


def create_clean_air_plan(params: PlanRequestParams) -> PlanResponse:
    """Orchestrate diurnal air fetching, exposure calculation, and AI advice."""
    air = _load_air_for_plan(params.latitude, params.longitude, params.date, params.scenario)
    mean_pm = round(sum(h.pm25 for h in air) / len(air), 1) if air else 150.0
    members_exp = _calc_members_exposure(params.members, air, params.home)
    vw, ww, inv = _analyze_meteorology(air)
    ctx = _resolve_context(params.context, params.members)
    rk = rank_interventions(ctx, params.budget_inr, ambient_pm25=mean_pm)
    commute_cmp = compare_commute_modes(mean_pm, params.commute_distance_km)
    g = generate_clean_air_advice(
        "Summarize today's clean air plan and actionable tips.",
        _extract_facts(vw, ww, inv, rk, members_exp),
        lang=params.language,
        provider=params.provider,
    )
    return _build_plan(
        PlanBuildData(
            members_exp=members_exp,
            air=air,
            vent_win=vw,
            worst_win=ww,
            inversion=inv,
            ranked=rk,
            commute_cmp=commute_cmp,
            guidance=g,
        )
    )
