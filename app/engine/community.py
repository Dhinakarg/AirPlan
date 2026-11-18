"""Community-level aggregation and shared clean-air space modeling."""

from collections.abc import Sequence
from typing import Final

from app.constants import (
    COMMUNITY_AVERAGE_TRIP_KM,
    COMMUNITY_CO2_KG_PER_KM_CAR,
    COMMUNITY_PM25_QUALITATIVE_NOTE,
)
from app.engine.models import CommunityImpact, Pledge

TRIP_REDUCING_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "carpool",
        "metro",
        "metro_instead_of_car",
        "combine_errands",
        "transit",
        "telework",
        "cycle_commute",
    }
)


def _empty_community_impact() -> CommunityImpact:
    """Return zeroed community impact record when no pledges are registered."""
    return CommunityImpact(
        trips_avoided=0,
        km_avoided=0.0,
        co2_kg_avoided=0.0,
        participating_households=0,
        pm25_note=COMMUNITY_PM25_QUALITATIVE_NOTE,
    )


def aggregate_pledges(pledges: Sequence[Pledge]) -> CommunityImpact:
    """Aggregate privacy-preserving community pledges into emissions metrics."""
    if not pledges:
        return _empty_community_impact()

    trips = sum(p.count for p in pledges if p.action in TRIP_REDUCING_ACTIONS)
    km = round(float(trips) * COMMUNITY_AVERAGE_TRIP_KM, 2)
    co2 = round(km * COMMUNITY_CO2_KG_PER_KM_CAR, 2)
    return CommunityImpact(
        trips_avoided=trips,
        km_avoided=km,
        co2_kg_avoided=co2,
        participating_households=len(pledges),
        pm25_note=COMMUNITY_PM25_QUALITATIVE_NOTE,
    )
