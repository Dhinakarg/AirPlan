"""Unit tests for emergency medical red-flag detection across English and Hindi."""

import pytest

from app.constants import RED_FLAG_OVERRIDE_ACTION
from app.engine.safety_rules import detect_red_flags


@pytest.mark.parametrize(
    ("query", "expected_symptom"),
    [
        ("I am experiencing sharp chest pain and sweating.", "chest_pain"),
        ("Patient having severe difficulty breathing while resting.", "breathing_difficulty"),
        ("My mother passed out on the balcony.", "fainting"),
        ("The toddler has blue lips and pale fingernails.", "cyanosis_blue_lips"),
        ("He is coughing up blood this morning.", "hemoptysis"),
    ],
)
def test_detect_red_flags_english_positive_symptoms(query: str, expected_symptom: str) -> None:
    """Detects emergency clinical red flags in English with immediate triage action."""
    res = detect_red_flags(query)
    assert res is not None
    assert res.symptom == expected_symptom
    assert res.urgency == "immediate"
    assert res.action == RED_FLAG_OVERRIDE_ACTION
    assert res.language == "en"


def test_detect_red_flags_english_negations() -> None:
    """Negated symptoms are correctly screened out and do not trigger medical red flags."""
    assert detect_red_flags("I have no chest pain today.") is None
    assert detect_red_flags("Patient arrived without difficulty breathing.") is None
    assert detect_red_flags("Not fainting, just felt a bit lightheaded earlier.") is None
    assert detect_red_flags("Denies shortness of breath or cough.") is None
    assert detect_red_flags("Zero chest tightness reported.") is None


@pytest.mark.parametrize(
    ("query", "expected_symptom"),
    [
        ("मुझे सीने में दर्द हो रहा है और घबराहट है।", "chest_pain"),
        ("मरीज को सांस लेने में तकलीफ हो रही है।", "breathing_difficulty"),
        ("दादाजी अचानक बेहोश हो गए।", "fainting"),
        ("बच्चे के होंठ नीले पड़ रहे हैं।", "cyanosis_blue_lips"),
    ],
)
def test_detect_red_flags_hindi_positive_symptoms(query: str, expected_symptom: str) -> None:
    """Detects emergency clinical red flags in Hindi (Devanagari)."""
    res = detect_red_flags(query)
    assert res is not None
    assert res.symptom == expected_symptom
    assert res.action == RED_FLAG_OVERRIDE_ACTION
    assert res.language == "hi"

    res5 = detect_red_flags("खांसी में खून आ रहा है।")
    assert res5 is not None
    assert res5.symptom == "hemoptysis"
    assert res5.language == "hi"


def test_detect_red_flags_hindi_negations() -> None:
    """Negated symptoms in Hindi do not trigger emergency red flags."""
    assert detect_red_flags("सीने में दर्द नहीं है।") is None
    assert detect_red_flags("सांस लेने में कोई तकलीफ नहीं है।") is None
    assert detect_red_flags("बिना किसी सांस की तकलीफ के।") is None


def test_detect_red_flags_benign_general_inquiries() -> None:
    """Standard air quality and planning queries return None without false alarms."""
    assert detect_red_flags("What is the best time to open windows today?") is None
    assert detect_red_flags("How do I make a DIY Corsi-Rosenthal box?") is None
    assert detect_red_flags("आज हवा का स्तर कैसा है?") is None
    assert detect_red_flags("") is None
    assert detect_red_flags("   ") is None
