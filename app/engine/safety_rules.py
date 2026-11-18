"""Heuristic safety boundaries, symptom screening, and clinical red-flag triggers."""

import re
from typing import Final, Literal

from app.constants import RED_FLAG_OVERRIDE_ACTION
from app.engine.models import RedFlag

# English symptom patterns mapped to canonical symptom labels
ENGLISH_SYMPTOM_PATTERNS: Final[tuple[tuple[str, str, Literal["immediate", "urgent"]], ...]] = (
    ("chest pain", "chest_pain", "immediate"),
    ("pain in chest", "chest_pain", "immediate"),
    ("chest tightness", "chest_tightness", "urgent"),
    ("difficulty breathing", "breathing_difficulty", "immediate"),
    ("cannot breathe", "breathing_difficulty", "immediate"),
    ("shortness of breath", "shortness_of_breath", "urgent"),
    ("struggling to breathe", "breathing_difficulty", "immediate"),
    ("gasping for air", "breathing_difficulty", "immediate"),
    ("fainting", "fainting", "immediate"),
    ("passed out", "fainting", "immediate"),
    ("loss of consciousness", "fainting", "immediate"),
    ("blue lips", "cyanosis_blue_lips", "immediate"),
    ("bluish lips", "cyanosis_blue_lips", "immediate"),
    ("coughing up blood", "hemoptysis", "immediate"),
    ("blood in cough", "hemoptysis", "immediate"),
)

# Hindi (Devanagari) symptom patterns
HINDI_SYMPTOM_PATTERNS: Final[tuple[tuple[str, str, Literal["immediate", "urgent"]], ...]] = (
    ("छाती में दर्द", "chest_pain", "immediate"),
    ("सीने में दर्द", "chest_pain", "immediate"),
    ("सांस लेने में तकलीफ", "breathing_difficulty", "immediate"),
    ("सांस फूलना", "shortness_of_breath", "urgent"),
    ("सांस लेने में कठिनाई", "breathing_difficulty", "immediate"),
    ("दम घुटना", "breathing_difficulty", "immediate"),
    ("बेहोश", "fainting", "immediate"),
    ("बेहोशी", "fainting", "immediate"),
    ("होंठ नीले", "cyanosis_blue_lips", "immediate"),
    ("नीले होंठ", "cyanosis_blue_lips", "immediate"),
    ("खांसी में खून", "hemoptysis", "immediate"),
    ("खून की उल्टी", "hemoptysis", "immediate"),
)

NEGATION_REGEX_EN: Final[re.Pattern[str]] = re.compile(
    r"\b(no|not|without|denies|zero|never)\b", re.IGNORECASE
)
NEGATION_REGEX_HI: Final[re.Pattern[str]] = re.compile(r"(नहीं|ना|बिना|कोई नहीं)")


def _is_negated_english(text: str, start_idx: int) -> bool:
    """Check if preceding tokens in the clause negate the symptom."""
    lookback = max(0, start_idx - 30)
    preceding = text[lookback:start_idx].lower()
    last_stop = max(preceding.rfind("."), preceding.rfind(";"), preceding.rfind(","))
    clause = preceding[last_stop + 1 :] if last_stop != -1 else preceding
    return bool(NEGATION_REGEX_EN.search(clause))


def _is_negated_hindi(text: str, start_idx: int, end_idx: int) -> bool:
    """Check if preceding or immediately following Hindi tokens negate the symptom."""
    pre_window = text[max(0, start_idx - 25) : start_idx]
    post_window = text[end_idx : min(len(text), end_idx + 25)]
    return bool(NEGATION_REGEX_HI.search(pre_window) or NEGATION_REGEX_HI.search(post_window))


def _scan_patterns(
    lowered: str,
    patterns: tuple[tuple[str, str, Literal["immediate", "urgent"]], ...],
    lang: Literal["en", "hi"],
) -> RedFlag | None:
    """Scan lowered text for target patterns and check negation."""
    for phrase, label, urgency in patterns:
        idx = lowered.find(phrase)
        if idx == -1:
            continue
        negated = (
            _is_negated_hindi(lowered, idx, idx + len(phrase))
            if lang == "hi"
            else _is_negated_english(lowered, idx)
        )
        if not negated:
            return RedFlag(
                symptom=label,
                urgency=urgency,
                action=RED_FLAG_OVERRIDE_ACTION,
                language=lang,
            )
    return None


def detect_red_flags(text: str) -> RedFlag | None:
    """Analyze input text for clinical red-flag symptoms in English and Hindi.

    When detected, directives to seek immediate medical emergency care strictly
    override all atmospheric planning and indoor intervention advice.

    Args:
        text: Free-text health inquiry or user description.

    Returns:
        RedFlag instance if severe symptom detected without negation, else None.
    """
    if not text.strip():
        return None

    lowered = text.lower()
    hindi_match = _scan_patterns(lowered, HINDI_SYMPTOM_PATTERNS, "hi")
    if hindi_match is not None:
        return hindi_match

    return _scan_patterns(lowered, ENGLISH_SYMPTOM_PATTERNS, "en")
