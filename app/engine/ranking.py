"""Cost-effectiveness evaluation and intervention ranking algorithms."""

from collections.abc import Sequence

from app.constants import (
    COST_NORMALIZATION_INR,
    EFFORT_MAX,
    NAAQS_PM25_24H_LIMIT_UG_M3,
    SEVERE_SMOG_THRESHOLD_UG_M3,
)
from app.engine.interventions import get_default_catalog
from app.engine.models import (
    HouseholdContext,
    Intervention,
    RankedIntervention,
)

FEASIBILITY_BLOCKERS: dict[str, str] = {
    "requires_home_ownership": "owns_home",
    "requires_transit": "has_transit_access",
    "requires_car": "has_car",
}


def _is_blocked(intervention: Intervention, context: HouseholdContext) -> bool:
    """Check if any structural precondition is unmet."""
    return any(
        cond in intervention.feasibility_conditions and not getattr(context, attr)
        for cond, attr in FEASIBILITY_BLOCKERS.items()
    )


def compute_feasibility(intervention: Intervention, context: HouseholdContext) -> float:
    """Evaluate practical feasibility multiplier for an intervention given household context."""
    if _is_blocked(intervention, context):
        return 0.0
    if intervention.id == "stop_incense_coils" and not context.burns_incense_or_coils:
        return 0.0
    return 1.0


def compute_ranking_score(
    impact: float,
    feasibility: float,
    cost_inr: float,
    effort: int,
) -> float:
    """Compute normalized cost-effectiveness score."""
    cost_norm = cost_inr / COST_NORMALIZATION_INR
    effort_norm = float(effort) / EFFORT_MAX
    denominator = 1.0 + cost_norm + effort_norm
    return round((impact * feasibility) / denominator, 4)


def _build_rank_reason(rank: int, item: Intervention, score: float) -> str:
    """Construct plain-language justification for the assigned priority rank."""
    pct = round(item.impact * 100.0)
    if item.cost_inr_per_month == 0.0:
        return (
            f"Rank #{rank}: Free measure ({pct}% impact, effort {item.effort}/5) "
            f"maximizes cost-effectiveness with score {score:.3f}. {item.rationale}"
        )
    cost = round(item.cost_inr_per_month)
    return (
        f"Rank #{rank}: High cost-benefit ({pct}% impact at ₹{cost}/mo, "
        f"effort {item.effort}/5, score {score:.3f}). {item.rationale}"
    )


def _severity_multiplier(item_id: str, ambient_pm25: float | None) -> float:
    """Adjust intervention priority score based on ambient PM2.5 severity."""
    if ambient_pm25 is None:
        return 1.0
    protective_ids = {"n95_mask_commute", "diy_corsi_rosenthal", "purifier", "seal_door_gaps"}
    if ambient_pm25 >= SEVERE_SMOG_THRESHOLD_UG_M3:
        return 1.45 if item_id in protective_ids else 0.9
    if ambient_pm25 < NAAQS_PM25_24H_LIMIT_UG_M3:
        return 0.65 if item_id in protective_ids else 1.25
    return 1.0


def _filter_and_score(
    pool: Sequence[Intervention],
    context: HouseholdContext,
    budget_inr: float,
    ambient_pm25: float | None = None,
) -> list[tuple[float, str, Intervention, float]]:
    """Filter candidates by budget and feasibility and compute scoring tuples."""
    candidates: list[tuple[float, str, Intervention, float]] = []
    for item in pool:
        if item.cost_inr_per_month > budget_inr:
            continue
        feas = compute_feasibility(item, context)
        if feas <= 0.0:
            continue
        base_score = compute_ranking_score(item.impact, feas, item.cost_inr_per_month, item.effort)
        score = round(base_score * _severity_multiplier(item.id, ambient_pm25), 4)
        candidates.append((score, item.id, item, feas))
    candidates.sort(key=lambda t: (-t[0], t[1]))
    return candidates


def rank_interventions(
    context: HouseholdContext,
    budget_inr: float,
    catalog: Sequence[Intervention] | None = None,
    ambient_pm25: float | None = None,
) -> list[RankedIntervention]:
    """Score, filter by constraints and budget, and stably rank interventions."""
    pool = catalog if catalog is not None else get_default_catalog()
    candidates = _filter_and_score(pool, context, budget_inr, ambient_pm25)
    return [
        RankedIntervention(
            intervention=item,
            score=score,
            rank=idx,
            feasibility=feas,
            why_this_rank=_build_rank_reason(idx, item, score),
        )
        for idx, (score, _, item, feas) in enumerate(candidates, start=1)
    ]
