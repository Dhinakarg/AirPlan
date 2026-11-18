"""Cost-effectiveness evaluation and intervention ranking algorithms."""

from collections.abc import Sequence

from app.constants import COST_NORMALIZATION_INR, EFFORT_MAX
from app.engine.interventions import get_default_catalog
from app.engine.models import (
    HouseholdContext,
    Intervention,
    RankedIntervention,
)


def compute_feasibility(intervention: Intervention, context: HouseholdContext) -> float:
    """Evaluate practical feasibility multiplier for an intervention given household context.

    Args:
        intervention: The candidate intervention.
        context: Household physical and financial constraints.

    Returns:
        Feasibility scalar between 0.0 (infeasible) and 1.0 (fully feasible).
    """
    conditions = intervention.feasibility_conditions
    if "requires_home_ownership" in conditions and not context.owns_home:
        return 0.0
    if "requires_transit" in conditions and not context.has_transit_access:
        return 0.0
    if "requires_car" in conditions and not context.has_car:
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
    """Compute normalized cost-effectiveness score.

    Formula: score = impact * feasibility / (1 + cost_norm + effort_norm)

    Args:
        impact: Relative PM2.5 exposure reduction (0-1).
        feasibility: Feasibility multiplier (0-1).
        cost_inr: Estimated monthly expense in INR.
        effort: Subjective effort scale (1-5).

    Returns:
        Calculated score rounded to 4 decimal places.
    """
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


def rank_interventions(
    context: HouseholdContext,
    budget_inr: float,
    catalog: Sequence[Intervention] | None = None,
) -> list[RankedIntervention]:
    """Score, filter by constraints and budget, and stably rank interventions.

    Args:
        context: Household structural, transit, and demographic attributes.
        budget_inr: Monthly clean-air expenditure ceiling in INR.
        catalog: Optional sequence of interventions (defaults to catalog).

    Returns:
        List of RankedIntervention items ordered by descending score.
    """
    pool = catalog if catalog is not None else get_default_catalog()
    candidates: list[tuple[float, str, Intervention, float]] = []

    for item in pool:
        if item.cost_inr_per_month > budget_inr:
            continue
        feas = compute_feasibility(item, context)
        if feas <= 0.0:
            continue
        score = compute_ranking_score(item.impact, feas, item.cost_inr_per_month, item.effort)
        candidates.append((score, item.id, item, feas))

    # Stable deterministic sort: score descending, then id ascending
    candidates.sort(key=lambda t: (-t[0], t[1]))

    ranked: list[RankedIntervention] = []
    for idx, (score, _, item, feas) in enumerate(candidates, start=1):
        reason = _build_rank_reason(idx, item, score)
        ranked.append(
            RankedIntervention(
                intervention=item,
                score=score,
                rank=idx,
                feasibility=feas,
                why_this_rank=reason,
            )
        )
    return ranked
