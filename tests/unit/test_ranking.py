"""Unit and property tests for context-based intervention ranking."""

from hypothesis import given
from hypothesis import strategies as st

from app.engine.models import (
    CookingFuel,
    HouseholdContext,
)
from app.engine.ranking import rank_interventions


def test_golden_scenario_delhi_family() -> None:
    """Validate ranking for Delhi family with toddler, asthmatic grandparent, wood cooking."""
    context = HouseholdContext(
        owns_home=True,
        has_transit_access=True,
        has_car=True,
        has_smokers=False,
        has_asthma_or_heart=True,
        has_children=True,
        cooking_fuel=CookingFuel.WOOD,
        has_unvented_kitchen=True,
        burns_incense_or_coils=True,
    )
    budget_inr = 500.0
    ranked = rank_interventions(context, budget_inr)

    assert len(ranked) >= 3
    top_3_ids = [r.intervention.id for r in ranked[:3]]

    # High-impact free & affordable measures rank at the very top
    assert "shift_exercise_cleanest_hour" in top_3_ids
    assert "no_waste_burning" in top_3_ids

    # Purifier (₹1200/mo) is excluded because it exceeds ₹500 budget
    purifier_ids = [r.intervention.id for r in ranked if r.intervention.id == "purifier"]
    assert len(purifier_ids) == 0

    # Even at higher budget (e.g. ₹1500), free timing and wet mopping cost-effectiveness ranks high
    higher_budget_ranked = rank_interventions(context, budget_inr=1500.0)
    timing_rank = next(
        r.rank for r in higher_budget_ranked if r.intervention.id == "shift_exercise_cleanest_hour"
    )
    purifier_rank = next(r.rank for r in higher_budget_ranked if r.intervention.id == "purifier")
    # Timing (free) strictly outranks expensive commercial purifier on cost-benefit
    assert timing_rank < purifier_rank


def test_budget_zero_excludes_all_paid_items() -> None:
    """A zero budget permits only cost-free behavioral interventions."""
    context = HouseholdContext()
    ranked = rank_interventions(context, budget_inr=0.0)
    assert len(ranked) > 0
    for r in ranked:
        assert r.intervention.cost_inr_per_month == 0.0


def test_renter_constraint_excludes_structural_exhaust() -> None:
    """Renting households cannot execute capital structural modifications."""
    context = HouseholdContext(owns_home=False)
    ranked = rank_interventions(context, budget_inr=2000.0)
    exhaust_items = [r for r in ranked if r.intervention.id == "vented_exhaust"]
    assert len(exhaust_items) == 0


def test_transit_constraint_excludes_metro() -> None:
    """Households without rapid transit access do not receive metro recommendations."""
    context = HouseholdContext(has_transit_access=False)
    ranked = rank_interventions(context, budget_inr=1000.0)
    metro_items = [r for r in ranked if r.intervention.id == "metro_instead_of_car"]
    assert len(metro_items) == 0


def test_why_this_rank_string_contains_actual_factors() -> None:
    """Ranking explanation includes percentage impact, cost, effort, and rationale."""
    context = HouseholdContext()
    ranked = rank_interventions(context, budget_inr=1000.0)
    top = ranked[0]
    assert f"Rank #{top.rank}" in top.why_this_rank
    assert "% impact" in top.why_this_rank
    assert "effort" in top.why_this_rank


@given(
    st.floats(min_value=0.0, max_value=5000.0),
    st.booleans(),
    st.booleans(),
    st.booleans(),
)
def test_ranking_determinism_and_order_stability(
    budget: float,
    owns_home: bool,
    has_transit: bool,
    has_car: bool,
) -> None:
    """Ranking is deterministic, monotonically sorted by score, with contiguous ranks."""
    context = HouseholdContext(
        owns_home=owns_home,
        has_transit_access=has_transit,
        has_car=has_car,
    )
    ranked_1 = rank_interventions(context, budget)
    ranked_2 = rank_interventions(context, budget)

    # Determinism
    assert [r.intervention.id for r in ranked_1] == [r.intervention.id for r in ranked_2]

    # Monotonicity & 1-based contiguous indexing
    for i in range(len(ranked_1)):
        assert ranked_1[i].rank == i + 1
        if i > 0:
            assert ranked_1[i - 1].score >= ranked_1[i].score
