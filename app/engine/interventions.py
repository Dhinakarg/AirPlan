"""Catalog of typed behavioral, domestic, transit, and community interventions."""

from typing import Final

from app.engine.interventions_transit import (
    INTERVENTION_CARPOOL,
    INTERVENTION_COMBINE_ERRANDS,
    INTERVENTION_METRO,
    INTERVENTION_N95_MASK,
    INTERVENTION_NO_WASTE_BURNING,
)
from app.engine.models import (
    Intervention,
    InterventionCategory,
    Provenance,
)

INTERVENTION_SHIFT_EXERCISE: Final[Intervention] = Intervention(
    id="shift_exercise_cleanest_hour",
    title="Shift outdoor exercise to cleanest hour",
    category=InterventionCategory.TIMING,
    cost_inr_per_month=0.0,
    effort=2,
    impact=0.70,
    feasibility_conditions=[],
    rationale="Rescheduling exertion to afternoon solar PM2.5 dip reduces inhaled dose.",
    provenance=Provenance(
        text="Diurnal boundary layer expansion and physiological ventilation rate dynamics",
        confidence="high",
    ),
)

INTERVENTION_WET_MOPPING: Final[Intervention] = Intervention(
    id="wet_mopping",
    title="Daily wet mopping instead of dry sweeping",
    category=InterventionCategory.HOME,
    cost_inr_per_month=0.0,
    effort=2,
    impact=0.45,
    feasibility_conditions=[],
    rationale="Damp mopping captures settled dust instead of resuspending fine particulates.",
    provenance=Provenance(
        text="Surface dust resuspension and indoor deposition trials",
        confidence="high",
    ),
)

INTERVENTION_SEAL_DOOR_GAPS: Final[Intervention] = Intervention(
    id="seal_door_gaps",
    title="Seal door thresholds and window perimeter gaps",
    category=InterventionCategory.HOME,
    cost_inr_per_month=150.0,
    effort=2,
    impact=0.50,
    feasibility_conditions=[],
    rationale="Weather-stripping and draft stoppers reduce ambient smog crack infiltration.",
    provenance=Provenance(
        text="Building envelope infiltration reduction and air leakage measurements",
        confidence="medium",
    ),
)

INTERVENTION_CORSI_ROSENTHAL: Final[Intervention] = Intervention(
    id="corsi_rosenthal_box",
    title="DIY Corsi-Rosenthal box air cleaner",
    category=InterventionCategory.HOME,
    cost_inr_per_month=400.0,
    effort=3,
    impact=0.80,
    feasibility_conditions=[],
    rationale="Box fan with MERV-13 filters delivers high clean air rate at low amortized cost.",
    provenance=Provenance(
        text="Open-source low-cost filtration engineering benchmarks and aerosol trials",
        confidence="high",
    ),
)

INTERVENTION_PURIFIER: Final[Intervention] = Intervention(
    id="purifier",
    title="Commercial HEPA room air purifier",
    category=InterventionCategory.HOME,
    cost_inr_per_month=1200.0,
    effort=1,
    impact=0.85,
    feasibility_conditions=[],
    rationale="Certified HEPA filtration captures >=99.97% of airborne PM2.5 in closed rooms.",
    provenance=Provenance(
        text="HEPA standard certification and residential mass balance modeling",
        confidence="high",
    ),
)

INTERVENTION_VENTED_EXHAUST: Final[Intervention] = Intervention(
    id="vented_exhaust",
    title="Install exterior-vented kitchen exhaust chimney",
    category=InterventionCategory.HOME,
    cost_inr_per_month=700.0,
    effort=4,
    impact=0.75,
    feasibility_conditions=["requires_home_ownership"],
    rationale="Ducts cooking byproducts outside, preventing PM buildup across living rooms.",
    provenance=Provenance(
        text="Indoor combustion capture efficiency and residential ventilation trials",
        confidence="high",
    ),
)

INTERVENTION_STOP_INCENSE_COILS: Final[Intervention] = Intervention(
    id="stop_incense_coils",
    title="Stop indoor incense and mosquito coil burning",
    category=InterventionCategory.HOME,
    cost_inr_per_month=0.0,
    effort=1,
    impact=0.60,
    feasibility_conditions=[],
    rationale="Eliminates primary indoor smoldering combustion emitting dense fine particulates.",
    provenance=Provenance(
        text="Indoor combustion emission factor characterization literature",
        confidence="high",
    ),
)

INTERVENTION_CATALOG: Final[tuple[Intervention, ...]] = (
    INTERVENTION_SHIFT_EXERCISE,
    INTERVENTION_WET_MOPPING,
    INTERVENTION_SEAL_DOOR_GAPS,
    INTERVENTION_CORSI_ROSENTHAL,
    INTERVENTION_PURIFIER,
    INTERVENTION_VENTED_EXHAUST,
    INTERVENTION_STOP_INCENSE_COILS,
    INTERVENTION_METRO,
    INTERVENTION_CARPOOL,
    INTERVENTION_N95_MASK,
    INTERVENTION_COMBINE_ERRANDS,
    INTERVENTION_NO_WASTE_BURNING,
)


def get_default_catalog() -> tuple[Intervention, ...]:
    """Retrieve the standard immutable catalog of candidate clean-air interventions."""
    return INTERVENTION_CATALOG
