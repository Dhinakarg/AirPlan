"""Indoor pollution source diagnostics and emission rate estimation."""

from typing import Literal

from app.constants import INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3
from app.engine.models import (
    CookingFuel,
    HomeSurvey,
    KitchenExhaust,
    SourceFinding,
    SweepingType,
)

SourceStatus = Literal["suspected", "measured"]


def _eval_cooking(survey: HomeSurvey, status: SourceStatus) -> SourceFinding:
    """Evaluate cooking fuel and kitchen exhaust configuration."""
    if survey.cooking_fuel in {CookingFuel.WOOD, CookingFuel.BIOMASS}:
        exhaust_penalties = {
            KitchenExhaust.NONE: 0.95,
            KitchenExhaust.INTERNAL: 0.85,
            KitchenExhaust.VENTED: 0.60,
        }
        like = exhaust_penalties.get(survey.kitchen_exhaust, 0.90)
        fuel_val = survey.cooking_fuel.value
        exh_val = survey.kitchen_exhaust.value
        return SourceFinding(
            source="biomass_cooking",
            likelihood=like,
            evidence=f"Combustion of {fuel_val} with {exh_val} exhaust",
            status=status,
            fixes=[
                "Switch to induction or LPG cooktop",
                "Install exterior-vented exhaust chimney",
                "Isolate kitchen enclosure from living rooms",
            ],
        )

    exhaust_penalties = {
        KitchenExhaust.NONE: 0.50,
        KitchenExhaust.INTERNAL: 0.35,
        KitchenExhaust.VENTED: 0.15,
    }
    like = exhaust_penalties.get(survey.kitchen_exhaust, 0.40)
    fuel_val = survey.cooking_fuel.value
    exh_val = survey.kitchen_exhaust.value
    return SourceFinding(
        source="unvented_lpg_cooking",
        likelihood=like,
        evidence=f"Cooking with {fuel_val} and {exh_val} exhaust",
        status=status,
        fixes=[
            "Install ducted exterior kitchen exhaust",
            "Maintain continuous natural draft during stove operation",
        ],
    )


def _eval_combustion(survey: HomeSurvey, status: SourceStatus) -> list[SourceFinding]:
    """Evaluate intentional indoor combustion sources like incense, coils, and tobacco."""
    findings: list[SourceFinding] = []
    if survey.incense:
        findings.append(
            SourceFinding(
                source="incense_burning",
                likelihood=0.80,
                evidence="Regular indoor agarbatti or dhoop incense burning",
                status=status,
                fixes=[
                    "Discontinue indoor incense combustion during smog season",
                    "Switch to flameless electronic diffusers or floral offerings",
                ],
            )
        )
    if survey.mosquito_coil:
        findings.append(
            SourceFinding(
                source="mosquito_coil",
                likelihood=0.85,
                evidence="Smoldering mosquito coil combustion in sleeping quarters",
                status=status,
                fixes=[
                    "Replace smoldering coils with mechanical window mesh nets",
                    "Use sealed electrical liquid vaporizers placed away from beds",
                ],
            )
        )
    if survey.smokers:
        findings.append(
            SourceFinding(
                source="tobacco_smoke",
                likelihood=0.90,
                evidence="Active indoor cigarette, bidi, or hookah smoking",
                status=status,
                fixes=[
                    "Enforce strict 100% smoke-free indoor rule",
                    "Designate an outdoor smoking area far from building entrances",
                ],
            )
        )
    return findings


def _eval_cleaning_and_pets(
    survey: HomeSurvey,
    status: SourceStatus,
) -> list[SourceFinding]:
    """Evaluate resuspension of dust through sweeping and pet presence."""
    findings: list[SourceFinding] = []
    if survey.sweeping == SweepingType.DRY:
        findings.append(
            SourceFinding(
                source="dry_sweeping_resuspension",
                likelihood=0.65,
                evidence="Dry broom sweeping resuspending settled surface dust",
                status=status,
                fixes=[
                    "Switch immediately to damp wet mopping with microfiber mop",
                    "Cease dry broom agitation during high-pollution episodes",
                ],
            )
        )
    if survey.pets:
        findings.append(
            SourceFinding(
                source="pet_dander",
                likelihood=0.30,
                evidence="Furred domestic pets present in living areas",
                status=status,
                fixes=[
                    "Brush and groom pets in outdoor verandas",
                    "Wash pet bedding frequently in hot water",
                ],
            )
        )
    return findings


def score_sources(survey: HomeSurvey) -> list[SourceFinding]:
    """Analyze questionnaire responses to detect and prioritize indoor emission sources.

    Status becomes 'measured' only when an indoor reading exists AND exceeds
    the safety threshold; never claim detection otherwise.

    Args:
        survey: Household indoor source survey responses.

    Returns:
        List of identified SourceFinding records ordered by descending likelihood.
    """
    has_high_reading = (
        survey.indoor_pm25_reading is not None
        and survey.indoor_pm25_reading > INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3
    )
    status: SourceStatus = "measured" if has_high_reading else "suspected"

    findings: list[SourceFinding] = []
    is_solid_fuel = survey.cooking_fuel in {CookingFuel.WOOD, CookingFuel.BIOMASS}
    is_unvented = survey.kitchen_exhaust != KitchenExhaust.VENTED
    if is_solid_fuel or is_unvented:
        findings.append(_eval_cooking(survey, status))

    findings.extend(_eval_combustion(survey, status))
    findings.extend(_eval_cleaning_and_pets(survey, status))

    if not findings and has_high_reading:
        findings.append(
            SourceFinding(
                source="ambient_infiltration",
                likelihood=0.75,
                evidence=f"Indoor PM2.5 ({survey.indoor_pm25_reading} ug/m3) exceeds threshold",
                status="measured",
                fixes=[
                    "Seal leaky door thresholds and window gaps",
                    "Deploy HEPA room air purifier",
                ],
            )
        )

    return sorted(findings, key=lambda f: f.likelihood, reverse=True)
