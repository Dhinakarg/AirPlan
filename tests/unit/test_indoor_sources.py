"""Unit tests for indoor pollution questionnaire evaluation and source diagnostics."""

from app.constants import INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3
from app.engine.indoor_sources import score_sources
from app.engine.models import (
    CookingFuel,
    HomeSurvey,
    KitchenExhaust,
    SweepingType,
)


def test_indoor_sources_suspected_without_reading(sample_home_survey: HomeSurvey) -> None:
    """Combustion sources without sensor reading are marked strictly as 'suspected'."""
    findings = score_sources(sample_home_survey)
    assert len(findings) == 5
    for f in findings:
        assert f.status == "suspected"


def test_indoor_sources_measured_when_reading_exceeds_threshold() -> None:
    """Status transitions to 'measured' only when reading strictly exceeds threshold."""
    elevated_reading = INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3 + 45.0
    survey = HomeSurvey(
        cooking_fuel=CookingFuel.WOOD,
        kitchen_exhaust=KitchenExhaust.NONE,
        indoor_pm25_reading=elevated_reading,
    )
    findings = score_sources(survey)
    assert len(findings) >= 1
    assert findings[0].status == "measured"
    assert findings[0].source == "biomass_cooking"


def test_indoor_sources_suspected_when_reading_below_threshold() -> None:
    """Reading below threshold keeps status as 'suspected' despite active sources."""
    low_reading = INDOOR_PM25_ELEVATED_THRESHOLD_UG_M3 - 20.0
    survey = HomeSurvey(
        cooking_fuel=CookingFuel.LPG,
        kitchen_exhaust=KitchenExhaust.NONE,
        incense=True,
        indoor_pm25_reading=low_reading,
    )
    findings = score_sources(survey)
    for f in findings:
        assert f.status == "suspected"


def test_clean_habits_no_reading_yields_empty_findings() -> None:
    """Household with induction, vented exhaust, wet mopping, and no smoke has zero findings."""
    survey = HomeSurvey(
        cooking_fuel=CookingFuel.INDUCTION,
        kitchen_exhaust=KitchenExhaust.VENTED,
        incense=False,
        mosquito_coil=False,
        smokers=False,
        pets=False,
        sweeping=SweepingType.WET,
        indoor_pm25_reading=None,
    )
    findings = score_sources(survey)
    assert findings == []


def test_clean_habits_elevated_reading_detects_ambient_infiltration() -> None:
    """Elevated reading with clean indoor habits diagnoses outdoor ambient infiltration."""
    elevated_reading = 120.0
    survey = HomeSurvey(
        cooking_fuel=CookingFuel.INDUCTION,
        kitchen_exhaust=KitchenExhaust.VENTED,
        incense=False,
        mosquito_coil=False,
        smokers=False,
        pets=False,
        sweeping=SweepingType.WET,
        indoor_pm25_reading=elevated_reading,
    )
    findings = score_sources(survey)
    assert len(findings) == 1
    assert findings[0].source == "ambient_infiltration"
    assert findings[0].status == "measured"


def test_cooking_exhaust_mitigation_gradient() -> None:
    """Vented kitchen exhaust significantly reduces estimated emission likelihood."""
    survey_none = HomeSurvey(cooking_fuel=CookingFuel.WOOD, kitchen_exhaust=KitchenExhaust.NONE)
    survey_internal = HomeSurvey(
        cooking_fuel=CookingFuel.WOOD, kitchen_exhaust=KitchenExhaust.INTERNAL
    )
    survey_vented = HomeSurvey(cooking_fuel=CookingFuel.WOOD, kitchen_exhaust=KitchenExhaust.VENTED)

    f_none = score_sources(survey_none)[0]
    f_internal = score_sources(survey_internal)[0]
    f_vented = score_sources(survey_vented)[0]

    assert f_none.likelihood > f_internal.likelihood > f_vented.likelihood


def test_pet_dander_detected_when_pets_present() -> None:
    """Pet presence generates pet dander source finding with outdoor grooming fixes."""
    survey = HomeSurvey(
        cooking_fuel=CookingFuel.INDUCTION,
        kitchen_exhaust=KitchenExhaust.VENTED,
        pets=True,
        sweeping=SweepingType.WET,
    )
    findings = score_sources(survey)
    assert len(findings) == 1
    assert findings[0].source == "pet_dander"
    assert "pet" in findings[0].evidence.lower()
