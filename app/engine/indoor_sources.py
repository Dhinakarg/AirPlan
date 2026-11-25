"""Indoor pollution source diagnostics and emission rate estimation."""

from app.constants import (
    INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3,
    LIKELIHOOD_BIOMASS_DEFAULT,
    LIKELIHOOD_BIOMASS_INTERNAL_EXHAUST,
    LIKELIHOOD_BIOMASS_NO_EXHAUST,
    LIKELIHOOD_BIOMASS_VENTED_EXHAUST,
    LIKELIHOOD_DRY_SWEEPING,
    LIKELIHOOD_INCENSE_BURNING,
    LIKELIHOOD_LPG_DEFAULT,
    LIKELIHOOD_LPG_INTERNAL_EXHAUST,
    LIKELIHOOD_LPG_NO_EXHAUST,
    LIKELIHOOD_LPG_VENTED_EXHAUST,
    LIKELIHOOD_MOSQUITO_COIL,
    LIKELIHOOD_PET_DANDER,
    LIKELIHOOD_TOBACCO_SMOKE,
)
from app.engine.enums import CookingFuel, KitchenExhaust, SweepingType
from app.engine.models import HomeSurvey, SourceFinding
from app.engine.source_findings import (
    SourceStatus,
)
from app.engine.source_findings import (
    ambient_infiltration_finding as _ambient_infiltration_finding,
)
from app.engine.source_findings import (
    biomass_finding as _biomass_finding,
)
from app.engine.source_findings import (
    lpg_finding as _lpg_finding,
)

BIOMASS_EXHAUST_PENALTIES: dict[KitchenExhaust, float] = {
    KitchenExhaust.NONE: LIKELIHOOD_BIOMASS_NO_EXHAUST,
    KitchenExhaust.INTERNAL: LIKELIHOOD_BIOMASS_INTERNAL_EXHAUST,
    KitchenExhaust.VENTED: LIKELIHOOD_BIOMASS_VENTED_EXHAUST,
}

LPG_EXHAUST_PENALTIES: dict[KitchenExhaust, float] = {
    KitchenExhaust.NONE: LIKELIHOOD_LPG_NO_EXHAUST,
    KitchenExhaust.INTERNAL: LIKELIHOOD_LPG_INTERNAL_EXHAUST,
    KitchenExhaust.VENTED: LIKELIHOOD_LPG_VENTED_EXHAUST,
}


def _eval_cooking(survey: HomeSurvey, status: SourceStatus) -> SourceFinding:
    """Evaluate cooking fuel and kitchen exhaust configuration."""
    fuel_val = survey.cooking_fuel.value
    exh_val = survey.kitchen_exhaust.value
    if survey.cooking_fuel in {CookingFuel.WOOD, CookingFuel.BIOMASS}:
        like = BIOMASS_EXHAUST_PENALTIES.get(survey.kitchen_exhaust, LIKELIHOOD_BIOMASS_DEFAULT)
        return _biomass_finding(fuel_val, exh_val, like, status)
    like = LPG_EXHAUST_PENALTIES.get(survey.kitchen_exhaust, LIKELIHOOD_LPG_DEFAULT)
    return _lpg_finding(fuel_val, exh_val, like, status)


def _eval_incense(survey: HomeSurvey, status: SourceStatus) -> SourceFinding | None:
    """Evaluate agarbatti / dhoop combustion."""
    if not survey.incense:
        return None
    return SourceFinding(
        source="incense_burning",
        likelihood=LIKELIHOOD_INCENSE_BURNING,
        evidence="Regular indoor agarbatti or dhoop incense burning",
        status=status,
        fixes=[
            "Discontinue indoor incense combustion during smog season",
            "Switch to flameless electronic diffusers or floral offerings",
        ],
    )


def _eval_mosquito_coil(survey: HomeSurvey, status: SourceStatus) -> SourceFinding | None:
    """Evaluate smoldering mosquito coil combustion."""
    if not survey.mosquito_coil:
        return None
    return SourceFinding(
        source="mosquito_coil",
        likelihood=LIKELIHOOD_MOSQUITO_COIL,
        evidence="Smoldering mosquito coil combustion in sleeping quarters",
        status=status,
        fixes=[
            "Replace smoldering coils with mechanical window mesh nets",
            "Use sealed electrical liquid vaporizers placed away from beds",
        ],
    )


def _eval_smokers(survey: HomeSurvey, status: SourceStatus) -> SourceFinding | None:
    """Evaluate active indoor tobacco smoking."""
    if not survey.smokers:
        return None
    return SourceFinding(
        source="tobacco_smoke",
        likelihood=LIKELIHOOD_TOBACCO_SMOKE,
        evidence="Active indoor cigarette, bidi, or hookah smoking",
        status=status,
        fixes=[
            "Enforce strict 100% smoke-free indoor rule",
            "Designate an outdoor smoking area far from building entrances",
        ],
    )


def _eval_combustion(survey: HomeSurvey, status: SourceStatus) -> list[SourceFinding]:
    """Evaluate intentional indoor combustion sources like incense, coils, and tobacco."""
    helpers = (_eval_incense, _eval_mosquito_coil, _eval_smokers)
    return [finding for h in helpers if (finding := h(survey, status)) is not None]


def _eval_sweeping(survey: HomeSurvey, status: SourceStatus) -> SourceFinding | None:
    """Evaluate mechanical re-suspension from dry broom sweeping."""
    if survey.sweeping != SweepingType.DRY:
        return None
    return SourceFinding(
        source="dry_sweeping_resuspension",
        likelihood=LIKELIHOOD_DRY_SWEEPING,
        evidence="Dry broom sweeping resuspending settled surface dust",
        status=status,
        fixes=[
            "Switch immediately to damp wet mopping with microfiber mop",
            "Cease dry broom agitation during high-pollution episodes",
        ],
    )


def _eval_pets(survey: HomeSurvey, status: SourceStatus) -> SourceFinding | None:
    """Evaluate biological allergen and particulate dander reservoirs."""
    if not survey.pets:
        return None
    return SourceFinding(
        source="pet_dander",
        likelihood=LIKELIHOOD_PET_DANDER,
        evidence="Furred domestic pets present in living areas",
        status=status,
        fixes=[
            "Brush and groom pets in outdoor verandas",
            "Wash pet bedding frequently in hot water",
        ],
    )


def _eval_cleaning_and_pets(survey: HomeSurvey, status: SourceStatus) -> list[SourceFinding]:
    """Evaluate resuspension of dust through sweeping and pet presence."""
    helpers = (_eval_sweeping, _eval_pets)
    return [finding for h in helpers if (finding := h(survey, status)) is not None]


def _is_high_reading(survey: HomeSurvey) -> bool:
    """Check if indoor PM2.5 reading exceeds regulatory elevated threshold."""
    return (
        survey.indoor_pm25_reading is not None
        and survey.indoor_pm25_reading > INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3
    )


def _collect_findings(survey: HomeSurvey, status: SourceStatus) -> list[SourceFinding]:
    """Collect candidate findings from cooking, combustion, cleaning, and pets."""
    findings: list[SourceFinding] = []
    is_solid = survey.cooking_fuel in {CookingFuel.WOOD, CookingFuel.BIOMASS}
    is_unvented = survey.kitchen_exhaust != KitchenExhaust.VENTED
    if is_solid or is_unvented:
        findings.append(_eval_cooking(survey, status))
    findings.extend(_eval_combustion(survey, status))
    findings.extend(_eval_cleaning_and_pets(survey, status))
    return findings


def score_sources(survey: HomeSurvey) -> list[SourceFinding]:
    """Analyze questionnaire responses to detect and prioritize indoor emission sources.

    Status becomes 'measured' only when an indoor reading exists AND exceeds
    the safety threshold; never claim detection otherwise.
    """
    has_high = _is_high_reading(survey)
    status: SourceStatus = "measured" if has_high else "suspected"
    findings = _collect_findings(survey, status)

    if not findings and has_high and survey.indoor_pm25_reading is not None:
        findings.append(_ambient_infiltration_finding(survey.indoor_pm25_reading))

    return sorted(findings, key=lambda f: f.likelihood, reverse=True)
