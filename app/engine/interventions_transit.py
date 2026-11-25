"""Transit and community clean-air intervention definitions."""

from typing import Final

from app.engine.models import Intervention, InterventionCategory, Provenance

INTERVENTION_METRO: Final[Intervention] = Intervention(
    id="metro_instead_of_car",
    title="Take metro instead of driving private car",
    category=InterventionCategory.TRANSPORT,
    cost_inr_per_month=800.0,
    effort=2,
    impact=0.50,
    feasibility_conditions=["requires_transit"],
    rationale="Filtered metro cabins bypass dense vehicular exhaust plumes on road corridors.",
    provenance=Provenance(
        text="Urban transit microenvironment particulate monitoring studies",
        confidence="medium",
    ),
)

INTERVENTION_CARPOOL: Final[Intervention] = Intervention(
    id="carpool",
    title="Carpool with colleagues or neighbors",
    category=InterventionCategory.TRANSPORT,
    cost_inr_per_month=400.0,
    effort=2,
    impact=0.35,
    feasibility_conditions=["requires_car"],
    rationale="Reduces vehicle trips, fuel expenditure, and roadway traffic density.",
    provenance=Provenance(
        text="Vehicle occupancy scaling and urban congestion exposure studies",
        confidence="medium",
    ),
)

INTERVENTION_N95_MASK: Final[Intervention] = Intervention(
    id="n95_mask_commute",
    title="Wear fit-checked N95/FFP2 respirator for commute",
    category=InterventionCategory.TRANSPORT,
    cost_inr_per_month=250.0,
    effort=2,
    impact=0.75,
    feasibility_conditions=[],
    rationale="Certified N95 respirators filter >=95% of inhaled roadway particulates.",
    provenance=Provenance(
        text="NIOSH/EN149 particulate respirator filtration efficiency tests",
        confidence="high",
    ),
)

INTERVENTION_COMBINE_ERRANDS: Final[Intervention] = Intervention(
    id="combine_errands",
    title="Combine outdoor errands into a single trip",
    category=InterventionCategory.TRANSPORT,
    cost_inr_per_month=0.0,
    effort=1,
    impact=0.30,
    feasibility_conditions=[],
    rationale="Consolidating tasks minimizes total duration spent in hazardous outdoor air.",
    provenance=Provenance(
        text="Exposure duration proportionality in ambient air toxicology",
        confidence="high",
    ),
)

INTERVENTION_NO_WASTE_BURNING: Final[Intervention] = Intervention(
    id="no_waste_burning",
    title="Community reporting to prevent waste burning",
    category=InterventionCategory.COMMUNITY,
    cost_inr_per_month=0.0,
    effort=2,
    impact=0.70,
    feasibility_conditions=[],
    rationale="Halting waste fires prevents severe ground-level smoke plumes during winter.",
    provenance=Provenance(
        text="Source apportionment receptor modeling for North Indian winter smog",
        confidence="high",
    ),
)
