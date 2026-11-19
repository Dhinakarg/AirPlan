"""Unit tests for community pledge aggregation and collective emissions impact."""

from app.constants import (
    COMMUNITY_AVERAGE_TRIP_KM,
    COMMUNITY_CO2_KG_PER_KM_CAR,
    COMMUNITY_PM25_QUALITATIVE_NOTE,
    MAX_PLEDGE_ENTRIES,
)
from app.engine.community import aggregate_pledges
from app.engine.models import Pledge
from app.services.community_service import (
    clear_pledges,
    get_community_summary,
    record_pledge,
    set_pledge_store_capacity,
)


def test_aggregate_pledges_empty() -> None:
    """Empty pledge list produces zeroed metrics with standard qualitative note."""
    impact = aggregate_pledges([])
    assert impact.trips_avoided == 0
    assert impact.km_avoided == 0.0
    assert impact.co2_kg_avoided == 0.0
    assert impact.participating_households == 0
    assert impact.pm25_note == COMMUNITY_PM25_QUALITATIVE_NOTE


def test_aggregate_pledges_transit_math() -> None:
    """Accurately calculates avoided vehicle kilometers and carbon emissions from pledges."""
    pledges = [
        Pledge(area_code="DL-01", action="carpool", count=5),
        Pledge(area_code="DL-02", action="metro", count=10),
    ]
    impact = aggregate_pledges(pledges)

    expected_trips = 15
    expected_km = round(15 * COMMUNITY_AVERAGE_TRIP_KM, 2)
    expected_co2 = round(expected_km * COMMUNITY_CO2_KG_PER_KM_CAR, 2)

    assert impact.trips_avoided == expected_trips
    assert impact.km_avoided == expected_km
    assert impact.co2_kg_avoided == expected_co2
    assert impact.participating_households == 2


def test_aggregate_pledges_non_trip_actions() -> None:
    """Non-transit community pledges count toward households but not vehicle trip reductions."""
    pledges = [
        Pledge(area_code="DL-03", action="no_waste_burning", count=1),
        Pledge(area_code="DL-04", action="no_waste_burning", count=1),
    ]
    impact = aggregate_pledges(pledges)
    assert impact.trips_avoided == 0
    assert impact.km_avoided == 0.0
    assert impact.co2_kg_avoided == 0.0
    assert impact.participating_households == 2


def test_community_pm25_note_is_strictly_qualitative() -> None:
    """Note must explicitly state emission reduction is qualitative and not measured PM2.5."""
    pledges = [Pledge(area_code="DL-05", action="carpool", count=2)]
    impact = aggregate_pledges(pledges)
    assert impact.pm25_note == "may reduce local traffic emissions; not a measured PM2.5 change"
    assert "not a measured PM2.5 change" in impact.pm25_note


def test_pledge_store_eviction_when_capacity_exceeded() -> None:
    """Oldest entries are evicted FIFO when pledge store reaches maximum bounded capacity."""
    clear_pledges()
    test_capacity = 3
    set_pledge_store_capacity(test_capacity)

    try:
        record_pledge(Pledge(area_code="DL-01", action="metro", count=1))
        record_pledge(Pledge(area_code="DL-02", action="metro", count=2))
        record_pledge(Pledge(area_code="DL-03", action="metro", count=3))

        summary = get_community_summary()
        assert summary.participating_households == 3
        assert summary.trips_avoided == 6

        # Adding 4th entry should evict DL-01 (count=1)
        record_pledge(Pledge(area_code="DL-04", action="metro", count=4))
        updated_summary = get_community_summary()
        assert updated_summary.participating_households == 3
        # Remaining: DL-02 (2) + DL-03 (3) + DL-04 (4) = 9
        assert updated_summary.trips_avoided == 9

        # DL-01 should no longer be present
        evicted_summary = get_community_summary(area_code="DL-01")
        assert evicted_summary.participating_households == 0
    finally:
        set_pledge_store_capacity(MAX_PLEDGE_ENTRIES)
        clear_pledges()
