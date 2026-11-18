"""Pure physical exposure calculation and comparative routine analysis."""

from app.constants import (
    ACTIVITY_BREATHING_RATES_ADULT,
    AGE_GROUP_BREATHING_MULTIPLIERS,
    BASELINE_EXPOSURE_INDEX,
    COMMUTE_MODE_FACTORS,
    INFILTRATION_FACTORS,
    MODE_FACTOR_OUTDOOR,
    OPEN_WINDOW_FACTOR,
    PURIFIER_FACTOR,
)
from app.engine.models import (
    Activity,
    AgeGroup,
    BlockDelta,
    ConfidenceLevel,
    DayExposure,
    HomeProfile,
    HourExposure,
    HourlyAir,
    Mode,
    Provenance,
    RoutineBlock,
    RoutineComparison,
)


def breathing_rate_m3_per_h(activity: Activity, age_group: AgeGroup) -> float:
    """Calculate physiological breathing rate in m3/h for activity and age.

    Args:
        activity: Physical activity type.
        age_group: Demographic age category.

    Returns:
        Minute ventilation volume in cubic meters per hour.
    """
    base = ACTIVITY_BREATHING_RATES_ADULT[activity.value]
    scale = AGE_GROUP_BREATHING_MULTIPLIERS[age_group.value]
    return round(base * scale, 4)


def get_microenvironment_factor(
    mode: Mode,
    hour: int,
    home: HomeProfile,
) -> tuple[float, Provenance]:
    """Determine effective particulate attenuation factor for a microenvironment.

    Args:
        mode: Transit or residential location mode.
        hour: Hour index (0-23).
        home: Household structural profile.

    Returns:
        Tuple of (microenvironment_factor, provenance).
    """
    if mode == Mode.HOME:
        if hour in home.windows_open_hours:
            prov = Provenance(text="Open windows natural ventilation factor", confidence="medium")
            return OPEN_WINDOW_FACTOR, prov
        infil = INFILTRATION_FACTORS[home.leakiness.value]
        pur = PURIFIER_FACTOR if home.purifier else 1.0
        conf: ConfidenceLevel = "high" if home.purifier else "medium"
        prov = Provenance(text="Indoor envelope infiltration and filtration", confidence=conf)
        return round(infil * pur, 4), prov

    if mode.value in COMMUTE_MODE_FACTORS:
        factor = COMMUTE_MODE_FACTORS[mode.value]
        prov = Provenance(text="Commute vehicle transit factor", confidence="low")
        return factor, prov

    prov = Provenance(text="Outdoor ambient exposure factor", confidence="high")
    return MODE_FACTOR_OUTDOOR, prov


def inhaled_dose_ug(
    pm25_ug_m3: float,
    microenvironment_factor: float,
    breathing_rate: float,
) -> float:
    """Calculate inhaled particulate mass dose for a 1-hour interval.

    Args:
        pm25_ug_m3: Ambient PM2.5 in ug/m3.
        microenvironment_factor: Micro-environment factor.
        breathing_rate: Breathing rate in m3/h.

    Returns:
        Inhaled particulate mass in micrograms (ug).
    """
    dose = pm25_ug_m3 * microenvironment_factor * breathing_rate
    return round(max(0.0, dose), 4)


def resolve_hour_block(hour: int, routine: list[RoutineBlock]) -> RoutineBlock:
    """Find the matching routine block for a given hour index.

    Args:
        hour: Hour index (0-23).
        routine: List of routine blocks.

    Returns:
        Matching RoutineBlock or default home rest block.
    """
    for block in routine:
        if block.start_hour <= hour < block.end_hour:
            return block
    return RoutineBlock(start_hour=hour, end_hour=hour + 1, activity=Activity.REST, mode=Mode.HOME)


def calculate_hour_exposure(
    air: HourlyAir,
    block: RoutineBlock,
    home: HomeProfile,
    age_group: AgeGroup,
) -> HourExposure:
    """Compute particulate exposure for a single hour.

    Args:
        air: Ambient air reading.
        block: Active routine block.
        home: Household structural profile.
        age_group: Demographic age group.

    Returns:
        Populated HourExposure model.
    """
    m_factor, prov = get_microenvironment_factor(block.mode, air.hour, home)
    b_rate = breathing_rate_m3_per_h(block.activity, age_group)
    dose = inhaled_dose_ug(air.pm25, m_factor, b_rate)

    return HourExposure(
        hour=air.hour,
        pm25_ug_m3=air.pm25,
        microenvironment_factor=m_factor,
        breathing_rate_m3_per_h=b_rate,
        inhaled_dose_ug=dose,
        mode=block.mode,
        activity=block.activity,
        provenance=prov,
    )


def compute_relative_index(total_dose: float, reference_dose: float | None) -> float:
    """Calculate relative exposure index compared to baseline reference.

    Args:
        total_dose: Current routine total dose in ug.
        reference_dose: Baseline reference dose in ug, or None.

    Returns:
        Index rounded to 1 decimal place (baseline = 100.0).
    """
    if reference_dose is None:
        return BASELINE_EXPOSURE_INDEX
    if reference_dose <= 0.0:
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
    """Calculate 24-hour daily inhaled particulate dose and relative exposure index.

    Args:
        routine: List of daily routine blocks.
        air: 24-hour ambient air observations.
        home: Household profile.
        age_group: Individual age group.
        reference_dose: Baseline reference dose for relative index computation.

    Returns:
        DayExposure instance.
    """
    hourly_exposures = [
        calculate_hour_exposure(point, resolve_hour_block(point.hour, routine), home, age_group)
        for point in air
    ]
    total_dose = round(sum(h.inhaled_dose_ug for h in hourly_exposures), 2)
    index = compute_relative_index(total_dose, reference_dose)
    prov = Provenance(
        text="24-hour time-weighted microenvironmental inhaled dose",
        confidence="medium",
    )
    return DayExposure(
        total_dose_ug=total_dose,
        index=index,
        hours=hourly_exposures,
        provenance=prov,
    )


def compute_block_deltas(
    base: list[RoutineBlock],
    alt: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup,
) -> list[BlockDelta]:
    """Calculate individual block dose deltas between baseline and alternative routines.

    Args:
        base: Baseline routine blocks.
        alt: Alternative routine blocks.
        air: 24-hour ambient air points.
        home: Household profile.
        age_group: Demographic age group.

    Returns:
        List of BlockDelta objects.
    """
    deltas: list[BlockDelta] = []
    for b in base:
        b_air = [a for a in air if b.start_hour <= a.hour < b.end_hour]
        b_dose = sum(calculate_hour_exposure(a, b, home, age_group).inhaled_dose_ug for a in b_air)
        alt_dose = sum(
            calculate_hour_exposure(
                a, resolve_hour_block(a.hour, alt), home, age_group
            ).inhaled_dose_ug
            for a in b_air
        )
        saved = round(b_dose - alt_dose, 2)
        deltas.append(
            BlockDelta(
                block=b,
                baseline_dose_ug=round(b_dose, 2),
                alt_dose_ug=round(alt_dose, 2),
                dose_saved_ug=saved,
            )
        )
    return deltas


def compare_routines(
    base: list[RoutineBlock],
    alt: list[RoutineBlock],
    air: list[HourlyAir],
    home: HomeProfile,
    age_group: AgeGroup = AgeGroup.ADULT,
) -> RoutineComparison:
    """Compare baseline routine against an optimized alternative routine.

    Args:
        base: Baseline routine blocks.
        alt: Alternative routine blocks.
        air: 24-hour ambient air observations.
        home: Household structural profile.
        age_group: Individual age group.

    Returns:
        RoutineComparison with relative index, saved dose, and per-block deltas.
    """
    base_exp = calculate_day_exposure(base, air, home, age_group, reference_dose=None)
    alt_exp = calculate_day_exposure(
        alt, air, home, age_group, reference_dose=base_exp.total_dose_ug
    )
    saved = round(base_exp.total_dose_ug - alt_exp.total_dose_ug, 2)
    deltas = compute_block_deltas(base, alt, air, home, age_group)

    prov = Provenance(
        text="Comparative exposure index normalized against baseline routine",
        confidence="medium",
    )
    return RoutineComparison(
        index_before=BASELINE_EXPOSURE_INDEX,
        index_after=alt_exp.index,
        dose_saved_ug=saved,
        per_block_delta=deltas,
        provenance=prov,
    )
