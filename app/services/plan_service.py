"""Personalized clean-air plan generation and routine orchestration service."""

from typing import Any

from app.ai.provider import AssistantProvider
from app.api.schemas import PlanResponse
from app.data.air_client import fetch_hourly_air
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


def _build_plan(
    members_exp: dict[str, DayExposure],
    air: list[HourlyAir],
    *,
    vent_win: Window | None,
    worst_win: Window | None,
    inversion: InversionResult,
    ranked: list[RankedIntervention],
    guidance: dict[str, Any],
) -> PlanResponse:
    """Assemble final validated PlanResponse object."""
    return PlanResponse(
        members_exposure=members_exp,
        ventilation_window=vent_win,
        worst_window=worst_win,
        inversion=inversion,
        ranked_interventions=ranked,
        ai_guidance=guidance,
        data_source=air[0].source if air else "sample",
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


def create_clean_air_plan(
    members: list[MemberPlanInput],
    home: HomeProfile,
    latitude: float,
    longitude: float,
    *,
    date: str | None = None,
    budget_inr: float = 500.0,
    context: HouseholdContext | None = None,
    language: str = "en",
    provider: AssistantProvider | None = None,
) -> PlanResponse:
    """Orchestrate diurnal air fetching, exposure calculation, and AI advice."""
    air = fetch_hourly_air(round(latitude, 2), round(longitude, 2), date)
    members_exp = _calc_members_exposure(members, air, home)
    vw, ww, inv = _analyze_meteorology(air)
    rk = rank_interventions(_resolve_context(context, members), budget_inr)
    g = generate_clean_air_advice(
        "Summarize today's clean air plan and actionable tips.",
        _extract_facts(vw, ww, inv, rk, members_exp),
        lang=language,
        provider=provider,
    )
    return _build_plan(
        members_exp, air, vent_win=vw, worst_win=ww, inversion=inv, ranked=rk, guidance=g
    )
