"""Unit tests for emergency medical red-flag detection across English and Hindi."""

from app.constants import RED_FLAG_OVERRIDE_ACTION
from app.engine.safety_rules import detect_red_flags


def test_detect_red_flags_english_positive_symptoms() -> None:
    """Detects emergency clinical red flags in English with immediate triage action."""
    res1 = detect_red_flags("I am experiencing sharp chest pain and sweating.")
    assert res1 is not None
    assert res1.symptom == "chest_pain"
    assert res1.urgency == "immediate"
    assert res1.action == RED_FLAG_OVERRIDE_ACTION
    assert res1.language == "en"

    res2 = detect_red_flags("Patient having severe difficulty breathing while resting.")
    assert res2 is not None
    assert res2.symptom == "breathing_difficulty"
    assert res2.urgency == "immediate"

    res3 = detect_red_flags("My mother passed out on the balcony.")
    assert res3 is not None
    assert res3.symptom == "fainting"

    res4 = detect_red_flags("The toddler has blue lips and pale fingernails.")
    assert res4 is not None
    assert res4.symptom == "cyanosis_blue_lips"

    res5 = detect_red_flags("He is coughing up blood this morning.")
    assert res5 is not None
    assert res5.symptom == "hemoptysis"


def test_detect_red_flags_english_negations() -> None:
    """Negated symptoms are correctly screened out and do not trigger medical red flags."""
    assert detect_red_flags("I have no chest pain today.") is None
    assert detect_red_flags("Patient arrived without difficulty breathing.") is None
    assert detect_red_flags("Not fainting, just felt a bit lightheaded earlier.") is None
    assert detect_red_flags("Denies shortness of breath or cough.") is None
    assert detect_red_flags("Zero chest tightness reported.") is None


def test_detect_red_flags_hindi_positive_symptoms() -> None:
    """Detects emergency clinical red flags in Hindi (Devanagari)."""
    res1 = detect_red_flags("मुझे सीने में दर्द हो रहा है और घबराहट है।")
    assert res1 is not None
    assert res1.symptom == "chest_pain"
    assert res1.action == RED_FLAG_OVERRIDE_ACTION
    assert res1.language == "hi"

    res2 = detect_red_flags("मरीज को सांस लेने में तकलीफ हो रही है।")
    assert res2 is not None
    assert res2.symptom == "breathing_difficulty"
    assert res2.language == "hi"

    res3 = detect_red_flags("दादाजी अचानक बेहोश हो गए।")
    assert res3 is not None
    assert res3.symptom == "fainting"
    assert res3.language == "hi"

    res4 = detect_red_flags("बच्चे के होंठ नीले पड़ रहे हैं।")
    assert res4 is not None
    assert res4.symptom == "cyanosis_blue_lips"
    assert res4.language == "hi"

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
