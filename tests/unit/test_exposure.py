"""Unit and property tests for pure exposure modeling."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.constants import (
    ACTIVITY_BREATHING_RATES_ADULT,
    AGE_GROUP_BREATHING_MULTIPLIERS,
    COMMUTE_MODE_FACTORS,
    INFILTRATION_FACTORS,
)
from app.engine.exposure import (
    breathing_rate_m3_per_h,
    calculate_day_exposure,
    compare_routines,
    compute_relative_index,
    get_microenvironment_factor,
    inhaled_dose_ug,
    resolve_hour_block,
)
from app.engine.models import (
    Activity,
    AgeGroup,
    HomeProfile,
    HourlyAir,
    Mode,
    RoutineBlock,
)


@pytest.mark.parametrize(
    ("activity", "expected_rate"),
    list(ACTIVITY_BREATHING_RATES_ADULT.items()),
)
def test_breathing_rate_adult_activities(activity: str, expected_rate: float) -> None:
    """Validate baseline adult breathing rate table entries."""
    act_enum = Activity(activity)
    rate = breathing_rate_m3_per_h(act_enum, AgeGroup.ADULT)
    assert rate == expected_rate


@pytest.mark.parametrize(
    ("age_group", "multiplier"),
    list(AGE_GROUP_BREATHING_MULTIPLIERS.items()),
)
def test_breathing_rate_age_scaling(age_group: str, multiplier: float) -> None:
    """Validate demographic age multiplier scales breathing volume proportionately."""
    age_enum = AgeGroup(age_group)
    rate = breathing_rate_m3_per_h(Activity.REST, age_enum)
    expected = round(ACTIVITY_BREATHING_RATES_ADULT["rest"] * multiplier, 4)
    assert rate == expected


def test_breathing_rate_physiological_hierarchy() -> None:
    """Exertion increases ventilation rate; childhood growth increases lung volume."""
    assert (
        breathing_rate_m3_per_h(Activity.SLEEP, AgeGroup.ADULT)
        < breathing_rate_m3_per_h(Activity.REST, AgeGroup.ADULT)
        < breathing_rate_m3_per_h(Activity.LIGHT, AgeGroup.ADULT)
        < breathing_rate_m3_per_h(Activity.WALK, AgeGroup.ADULT)
        < breathing_rate_m3_per_h(Activity.EXERCISE, AgeGroup.ADULT)
    )
    assert (
        breathing_rate_m3_per_h(Activity.LIGHT, AgeGroup.TODDLER)
        < breathing_rate_m3_per_h(Activity.LIGHT, AgeGroup.CHILD)
        < breathing_rate_m3_per_h(Activity.LIGHT, AgeGroup.TEEN)
        < breathing_rate_m3_per_h(Activity.LIGHT, AgeGroup.ADULT)
    )


@pytest.mark.parametrize(
    ("mode_str", "expected_factor"),
    list(COMMUTE_MODE_FACTORS.items()),
)
def test_commute_mode_factors_parametrized(mode_str: str, expected_factor: float) -> None:
    """Validate transit mode factors match literature constants."""
    mode_enum = Mode(mode_str)
    home = HomeProfile()
    factor, prov = get_microenvironment_factor(mode_enum, hour=12, home=home)
    assert factor == expected_factor
    assert prov.confidence == "low"


def test_outdoor_microenvironment_factor() -> None:
    """Outdoor ambient microenvironment has factor 1.0 and high confidence."""
    home = HomeProfile()
    factor, prov = get_microenvironment_factor(Mode.OUTDOOR, hour=12, home=home)
    assert factor == 1.0
    assert prov.confidence == "high"


def test_purifier_lowers_indoor_dose(
    sample_diurnal_air: list[HourlyAir],
    sample_home_profiles: dict[str, HomeProfile],
    sample_routine: list[RoutineBlock],
) -> None:
    """Active purifier strictly reduces 24-hour total inhaled particulate dose."""
    tight_purifier = sample_home_profiles["tight_purifier"]
    tight_no_purifier = sample_home_profiles["tight_no_purifier"]

    dose_purifier = calculate_day_exposure(sample_routine, sample_diurnal_air, tight_purifier)
    dose_no_purifier = calculate_day_exposure(sample_routine, sample_diurnal_air, tight_no_purifier)

    assert dose_purifier.total_dose_ug < dose_no_purifier.total_dose_ug


def test_leakier_home_greater_dose(
    sample_diurnal_air: list[HourlyAir],
    sample_home_profiles: dict[str, HomeProfile],
    sample_routine: list[RoutineBlock],
) -> None:
    """Envelope leakiness strictly increases indoor particulate dose: leaky >= tight."""
    tight = sample_home_profiles["tight_no_purifier"]
    average = sample_home_profiles["average"]
    leaky = sample_home_profiles["leaky"]

    dose_tight = calculate_day_exposure(sample_routine, sample_diurnal_air, tight).total_dose_ug
    dose_avg = calculate_day_exposure(sample_routine, sample_diurnal_air, average).total_dose_ug
    dose_leaky = calculate_day_exposure(sample_routine, sample_diurnal_air, leaky).total_dose_ug

    assert dose_tight < dose_avg < dose_leaky


def test_open_windows_factor_applied(sample_home_profiles: dict[str, HomeProfile]) -> None:
    """Windows open hour applies open window factor of 0.90."""
    home = sample_home_profiles["open_windows"]
    factor_closed, _ = get_microenvironment_factor(Mode.HOME, hour=10, home=home)
    factor_open, _ = get_microenvironment_factor(Mode.HOME, hour=13, home=home)

    assert factor_closed == INFILTRATION_FACTORS["average"]
    assert factor_open == 0.90


def test_identical_routines_give_index_100(
    sample_diurnal_air: list[HourlyAir],
    sample_home_profiles: dict[str, HomeProfile],
    sample_routine: list[RoutineBlock],
) -> None:
    """Comparing identical routines must produce an index of exactly 100.0 and zero dose saved."""
    comparison = compare_routines(
        sample_routine,
        sample_routine,
        sample_diurnal_air,
        sample_home_profiles["average"],
    )
    assert comparison.index_before == 100.0
    assert comparison.index_after == 100.0
    assert comparison.dose_saved_ug == 0.0


def test_moving_exercise_from_high_pm_to_low_pm_lowers_index(
    sample_diurnal_air: list[HourlyAir],
    sample_home_profiles: dict[str, HomeProfile],
) -> None:
    """Shifting outdoor exercise from smog peak (05:00) to afternoon dip (13:00) lowers index."""
    # Morning peak smog at 05:00 (~390 ug/m3)
    base_routine = [
        RoutineBlock(start_hour=0, end_hour=5, activity=Activity.SLEEP, mode=Mode.HOME),
        RoutineBlock(start_hour=5, end_hour=6, activity=Activity.EXERCISE, mode=Mode.OUTDOOR),
        RoutineBlock(start_hour=6, end_hour=24, activity=Activity.REST, mode=Mode.HOME),
    ]
    # Shifted to afternoon dip at 13:00 (~75 ug/m3)
    alt_routine = [
        RoutineBlock(start_hour=0, end_hour=13, activity=Activity.REST, mode=Mode.HOME),
        RoutineBlock(start_hour=13, end_hour=14, activity=Activity.EXERCISE, mode=Mode.OUTDOOR),
        RoutineBlock(start_hour=14, end_hour=24, activity=Activity.REST, mode=Mode.HOME),
    ]
    comparison = compare_routines(
        base_routine,
        alt_routine,
        sample_diurnal_air,
        sample_home_profiles["average"],
    )
    assert comparison.index_after < 100.0
    assert comparison.dose_saved_ug > 0.0


def test_zero_baseline_division_guarded() -> None:
    """Zero baseline reference dose gracefully returns 100.0 without ZeroDivisionError."""
    assert compute_relative_index(total_dose=0.0, reference_dose=0.0) == 100.0
    assert compute_relative_index(total_dose=50.0, reference_dose=0.0) == 100.0
    assert compute_relative_index(total_dose=40.0, reference_dose=80.0) == 50.0


def test_resolve_hour_block_fallback() -> None:
    """Gaps in routine schedule fall back to default home rest."""
    routine = [RoutineBlock(start_hour=10, end_hour=12, activity=Activity.WALK, mode=Mode.WALK)]
    block_gap = resolve_hour_block(hour=5, routine=routine)
    assert block_gap.activity == Activity.REST
    assert block_gap.mode == Mode.HOME


@given(
    pm25=st.floats(min_value=0.0, max_value=1000.0),
    m_factor=st.floats(min_value=0.0, max_value=2.0),
    b_rate=st.floats(min_value=0.1, max_value=3.0),
)
def test_hypothesis_dose_non_negative(pm25: float, m_factor: float, b_rate: float) -> None:
    """Property: Inhaled dose is always non-negative for valid physical inputs."""
    dose = inhaled_dose_ug(pm25, m_factor, b_rate)
    assert dose >= 0.0


@given(
    pm25_low=st.floats(min_value=0.0, max_value=400.0),
    pm25_high=st.floats(min_value=400.1, max_value=1000.0),
    m_factor=st.floats(min_value=0.1, max_value=1.5),
    b_rate=st.floats(min_value=0.2, max_value=2.0),
)
def test_hypothesis_dose_monotonic_in_pm25(
    pm25_low: float,
    pm25_high: float,
    m_factor: float,
    b_rate: float,
) -> None:
    """Property: Inhaled dose is strictly non-decreasing with increasing ambient PM2.5."""
    dose_low = inhaled_dose_ug(pm25_low, m_factor, b_rate)
    dose_high = inhaled_dose_ug(pm25_high, m_factor, b_rate)
    assert dose_high >= dose_low
