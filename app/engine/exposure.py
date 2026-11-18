"""Aerosol exposure physics, microenvironment attenuation, and inhaled dose modeling."""

from app.constants import (
    ACTIVITY_BREATHING_RATES_M3_PER_H,
    AGE_GROUP_BREATHING_MULTIPLIERS,
    BASELINE_EXPOSURE_INDEX,
    COMMUTE_MODE_FACTORS,
    INFILTRATION_FACTORS,
    MODE_FACTOR_OUTDOOR,
    OPEN_WINDOW_FACTOR,
    PURIFIER_FACTOR,
)
from app.engine.enums import Activity, AgeGroup, Mode
from app.engine.models import (
    BlockDelta,
    ConfidenceLevel,
    DayExposure,
    HomeProfile,
    HourExposure,
    HourlyAir,
    Provenance,
    RoutineBlock,
    RoutineComparison,
)


def breathing_rate_m3_per_h(activity: Activity, age_group: AgeGroup) -> float:
    """Compute physical minute ventilation rate in cubic meters per hour."""
    base = ACTIVITY_BREATHING_RATES_M3_PER_H[activity.value]
    scale = AGE_GROUP_BREATHING_MULTIPLIERS[age_group.value]
    return float(round(base * scale, 4))


def _home_microenvironment_factor(hour: int, home: HomeProfile) -> tuple[float, Provenance]:
    """Calculate residential particulate attenuation with window and purifier effects."""
    if hour in home.windows_open_hours:
        return OPEN_WINDOW_FACTOR, Provenance(
            text="Open windows natural ventilation factor", confidence="medium"
        )
    infil = INFILTRATION_FACTORS[home.leakiness.value]
    pur = PURIFIER_FACTOR if home.purifier else 1.0
    conf: ConfidenceLevel = "high" if home.purifier else "medium"
    return round(infil * pur, 4), Provenance(
        text="Indoor envelope infiltration and filtration", confidence=conf
    )


def get_microenvironment_factor(
    mode: Mode, hour: int, home: HomeProfile
) -> tuple[float, Provenance]:
    """Determine effective particulate attenuation factor for a microenvironment."""
    if mode == Mode.HOME:
        return _home_microenvironment_factor(hour, home)
    if mode.value in COMMUTE_MODE_FACTORS:
        return COMMUTE_MODE_FACTORS[mode.value], Provenance(
            text="Commute vehicle transit factor", confidence="low"
        )
    return MODE_FACTOR_OUTDOOR, Provenance(
        text="Outdoor ambient exposure factor", confidence="high"
    )


def inhaled_dose_ug(
    pm25_ug_m3: float,
    microenvironment_factor: float,
    breathing_rate: float,
) -> float:
    """Calculate inhaled particulate mass dose for a 1-hour interval."""
    dose = pm25_ug_m3 * microenvironment_factor * breathing_rate
    return round(max(0.0, dose), 4)


def resolve_hour_block(hour: int, routine: list[RoutineBlock]) -> RoutineBlock:
    """Find the matching routine block for a given hour index."""
    for block in routine:
        if block.start_hour <= hour < block.end_hour:
            return block
    return RoutineBlock(start_hour=hour, end_hour=hour + 1, activity=Activity.REST, mode=Mode.HOME)


def calculate_hour_exposure(
    air: HourlyAir, block: RoutineBlock, home: HomeProfile, age_group: AgeGroup
) -> HourExposure:
    """Compute particulate exposure for a single hour."""
    m_factor, prov = get_microenvironment_factor(block.mode, air.hour, home)
    b_rate = breathing_rate_m3_per_h(block.activity, age_group)
    return HourExposure(
        hour=air.hour,
        pm25_ug_m3=air.pm25,
        microenvironment_factor=m_factor,
        breathing_rate_m3_per_h=b_rate,
        inhaled_dose_ug=inhaled_dose_ug(air.pm25, m_factor, b_rate),
        mode=block.mode,
        activity=block.activity,
        provenance=prov,
    )


def compute_relative_index(total_dose: float, reference_dose: float | None) -> float:
    """Calculate relative exposure index compared to baseline reference."""
    if reference_dose is None or reference_dose <= 0.0:
        return BASELINE_EXPOSURE_INDEX
    ratio = (total_dose / reference_dose) * BASELINE_EXPOSURE_INDEX
    return round(ratio, 1)


def calculate_day_exposure(
    routine: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup = AgeGroup.ADULT,
    reference_dose: float | None = None,
) -> DayExposure:
    """Calculate 24-hour daily inhaled particulate dose and relative exposure index."""
    hourly_exposures = [
        calculate_hour_exposure(pt, resolve_hour_block(pt.hour, routine), home, age_group)
        for pt in air
    ]
    total_dose = round(sum(h.inhaled_dose_ug for h in hourly_exposures), 2)
    return DayExposure(
        total_dose_ug=total_dose,
        index=compute_relative_index(total_dose, reference_dose),
        hours=hourly_exposures,
        provenance=Provenance(
            text="24-hour time-weighted microenvironmental inhaled dose", confidence="medium"
        ),
    )


def _compute_single_block_delta(
    b: RoutineBlock,
    alt: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup,
) -> BlockDelta:
    """Calculate dose delta for a single schedule interval."""
    b_air = [a for a in air if b.start_hour <= a.hour < b.end_hour]
    b_dose = sum(calculate_hour_exposure(a, b, home, age_group).inhaled_dose_ug for a in b_air)
    alt_dose = sum(
        calculate_hour_exposure(a, resolve_hour_block(a.hour, alt), home, age_group).inhaled_dose_ug
        for a in b_air
    )
    return BlockDelta(
        block=b,
        baseline_dose_ug=round(b_dose, 2),
        alt_dose_ug=round(alt_dose, 2),
        dose_saved_ug=round(b_dose - alt_dose, 2),
    )


def compute_block_deltas(
    base: list[RoutineBlock],
    alt: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup,
) -> list[BlockDelta]:
    """Calculate individual block dose deltas between baseline and alternative routines."""
    return [_compute_single_block_delta(b, alt, air, home, age_group) for b in base]


def compare_routines(
    base: list[RoutineBlock],
    alt: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup = AgeGroup.ADULT,
) -> RoutineComparison:
    """Compare baseline routine against an optimized alternative routine."""
    base_exp = calculate_day_exposure(base, air, home, age_group, reference_dose=None)
    alt_exp = calculate_day_exposure(
        alt, air, home, age_group, reference_dose=base_exp.total_dose_ug
    )
    return RoutineComparison(
        index_before=BASELINE_EXPOSURE_INDEX,
        index_after=alt_exp.index,
        dose_saved_ug=round(base_exp.total_dose_ug - alt_exp.total_dose_ug, 2),
        per_block_delta=compute_block_deltas(base, alt, air, home, age_group),
        provenance=Provenance(
            text="Comparative exposure index normalized against baseline routine",
            confidence="medium",
        ),
    )
