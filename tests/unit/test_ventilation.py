"""Unit tests for ventilation, inversion detection, and peak exposure windows."""

from hypothesis import given
from hypothesis import strategies as st

from app.constants import (
    INVERSION_BLH_M,
    OPEN_WINDOW_MAX_PM25_UG_M3,
    STAGNATION_HOURS,
    STAGNATION_WIND_KMH,
)
from app.engine.models import HourlyAir
from app.engine.ventilation import (
    detect_inversion,
    find_ventilation_window,
    worst_exposure_window,
)


def test_find_ventilation_window_optimal(sample_diurnal_air: list[HourlyAir]) -> None:
    """Finds lowest contiguous PM2.5 window during afternoon hours."""
    window = find_ventilation_window(sample_diurnal_air, min_hours=2)
    assert window is not None
    # In sample_diurnal_air, h=12 is 80, h=13 is 75 -> mean 77.5
    assert window.start_hour == 12
    assert window.end_hour == 14
    assert window.mean_pm25 == 77.5
    assert "Optimal" in window.reason


def test_find_ventilation_window_uniformly_bad_air() -> None:
    """Returns None when every hour exceeds open window threshold."""
    bad_air = [
        HourlyAir(
            hour=h,
            pm25=OPEN_WINDOW_MAX_PM25_UG_M3 + 50.0,
            wind_kmh=2.0,
            boundary_layer_m=150.0,
        )
        for h in range(24)
    ]
    assert find_ventilation_window(bad_air, min_hours=2) is None


def test_find_ventilation_window_mean_exceeds_threshold() -> None:
    """Returns None when isolated low hour cannot form qualifying contiguous window."""
    air = [
        HourlyAir(hour=0, pm25=90.0, wind_kmh=5.0, boundary_layer_m=None),
        HourlyAir(hour=1, pm25=150.0, wind_kmh=5.0, boundary_layer_m=None),
        HourlyAir(hour=2, pm25=200.0, wind_kmh=5.0, boundary_layer_m=None),
    ]
    # Slice [0, 1] mean = (90 + 150)/2 = 120 > 100
    assert find_ventilation_window(air, min_hours=2) is None


def test_find_ventilation_window_insufficient_length() -> None:
    """Returns None when input data has fewer hours than required min_hours."""
    short_air = [HourlyAir(hour=0, pm25=50.0, wind_kmh=10.0, boundary_layer_m=500.0)]
    assert find_ventilation_window(short_air, min_hours=2) is None


def test_find_ventilation_window_custom_duration(
    sample_diurnal_air: list[HourlyAir],
) -> None:
    """Correctly evaluates window with 3-hour minimum duration."""
    window = find_ventilation_window(sample_diurnal_air, min_hours=3)
    assert window is not None
    # h12: 80, h13: 75, h14: 85 -> mean 80.0
    assert window.start_hour == 12
    assert window.end_hour == 15
    assert window.mean_pm25 == 80.0


def test_detect_inversion_with_blh(sample_diurnal_air: list[HourlyAir]) -> None:
    """Flags hours where boundary layer height drops below INVERSION_BLH_M."""
    result = detect_inversion(sample_diurnal_air)
    assert result.method == "boundary_layer_height"
    assert len(result.hours) == 12
    assert 0 in result.hours
    assert 4 in result.hours
    assert 13 not in result.hours
    for h in result.hours:
        blh = sample_diurnal_air[h].boundary_layer_m
        assert blh is not None and blh < INVERSION_BLH_M


def test_detect_inversion_without_blh_stagnation_proxy(
    sample_stagnant_air_without_blh: list[HourlyAir],
) -> None:
    """Uses wind speed proxy during stagnation hours when BLH is absent."""
    result = detect_inversion(sample_stagnant_air_without_blh)
    assert result.method == "stagnation_proxy"
    assert len(result.hours) == 12
    for h in result.hours:
        assert h in STAGNATION_HOURS
        assert sample_stagnant_air_without_blh[h].wind_kmh < STAGNATION_WIND_KMH


def test_detect_inversion_clean_well_mixed_air() -> None:
    """Returns empty flagged list when BLH is deep throughout."""
    clean_air = [
        HourlyAir(hour=h, pm25=50.0, wind_kmh=15.0, boundary_layer_m=800.0) for h in range(24)
    ]
    result = detect_inversion(clean_air)
    assert result.method == "boundary_layer_height"
    assert result.hours == []


def test_detect_inversion_high_wind_stagnation_proxy() -> None:
    """Returns empty flagged list when winds are high during stagnation hours."""
    windy_air = [
        HourlyAir(hour=h, pm25=50.0, wind_kmh=20.0, boundary_layer_m=None) for h in range(24)
    ]
    result = detect_inversion(windy_air)
    assert result.method == "stagnation_proxy"
    assert result.hours == []


def test_worst_exposure_window_finds_peak(
    sample_diurnal_air: list[HourlyAir],
) -> None:
    """Identifies the worst contiguous smog peak window."""
    window = worst_exposure_window(sample_diurnal_air, min_hours=2)
    assert window is not None
    # Peak is h=3 (380.0) and h=4 (390.0) -> mean 385.0
    assert window.start_hour == 3
    assert window.end_hour == 5
    assert window.mean_pm25 == 385.0
    assert "Peak" in window.reason


def test_worst_exposure_window_insufficient_length() -> None:
    """Returns None when observation sequence is shorter than requested window."""
    short_air = [HourlyAir(hour=0, pm25=100.0, wind_kmh=5.0, boundary_layer_m=None)]
    assert worst_exposure_window(short_air, min_hours=2) is None


@given(
    st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=999.0),
            st.floats(min_value=0.0, max_value=50.0),
            st.one_of(st.none(), st.floats(min_value=50.0, max_value=2500.0)),
        ),
        min_size=2,
        max_size=24,
    )
)
def test_worst_exposure_window_hypothesis_bounds(
    data: list[tuple[float, float, float | None]],
) -> None:
    """Worst window mean is bounded by min and max hourly PM2.5 in sequence."""
    air = [
        HourlyAir(hour=i, pm25=pm, wind_kmh=w, boundary_layer_m=blh)
        for i, (pm, w, blh) in enumerate(data)
    ]
    window = worst_exposure_window(air, min_hours=2)
    assert window is not None
    pm_values = [pt.pm25 for pt in air]
    assert min(pm_values) - 0.1 <= window.mean_pm25 <= max(pm_values) + 0.1
    assert window.start_hour < window.end_hour


@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=23),
            st.floats(min_value=0.0, max_value=999.0),
            st.floats(min_value=0.0, max_value=50.0),
            st.one_of(st.none(), st.floats(min_value=10.0, max_value=2000.0)),
        ),
        min_size=1,
        max_size=24,
    )
)
def test_detect_inversion_hypothesis_properties(
    data: list[tuple[int, float, float, float | None]],
) -> None:
    """Inversion flagged hours are always a subset of provided hours."""
    air = [HourlyAir(hour=h, pm25=pm, wind_kmh=w, boundary_layer_m=blh) for h, pm, w, blh in data]
    result = detect_inversion(air)
    all_hours = {pt.hour for pt in air}
    assert set(result.hours).issubset(all_hours)
    assert result.method in {"boundary_layer_height", "stagnation_proxy"}
