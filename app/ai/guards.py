"""Prompt injection defenses, control character sanitization, and input guardrails."""

import re
from typing import Any, Final

INJECTION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?instructions", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior)\s+(rules|prompts)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an|in)?", re.IGNORECASE),
    re.compile(r"(jailbreak|dan\s+mode|developer\s+mode)", re.IGNORECASE),
    re.compile(r"(reveal|print|show|repeat)\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content)\s+filters", re.IGNORECASE),
    re.compile(r"(पुराने|पिछले)\s+निर्देश\s+भूल\s+जाओ"),
    re.compile(r"सिस्टम\s+प्रॉम्प्ट\s+(दिखाओ|बताओ)"),
)

CONTROL_CHAR_REGEX: Final[re.Pattern[str]] = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TAG_REGEX: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")


def sanitize_user_text(text: str, max_length: int = 500) -> str:
    """Sanitize untrusted user text by capping length, stripping control chars and tags.

    Args:
        text: Raw user input text.
        max_length: Maximum allowed character length.

    Returns:
        Sanitized safe string with tags stripped and whitespace normalized.
    """
    if not text:
        return ""
    # Strip dangerous ASCII control characters
    cleaned = CONTROL_CHAR_REGEX.sub("", text)
    # Strip HTML / XML tags to prevent escaping data boundaries
    cleaned = TAG_REGEX.sub("", cleaned)
    # Normalize whitespace and truncate
    trimmed = " ".join(cleaned.split())
    return trimmed[:max_length]


def looks_like_injection(text: str) -> bool:
    """Evaluate whether user input contains recognizable prompt injection patterns.

    Args:
        text: Raw or sanitized user text.

    Returns:
        True if text matches injection heuristics, False otherwise.
    """
    if not text:
        return False
    return any(pat.search(text) for pat in INJECTION_PATTERNS)


def build_injection_refusal(lang: str = "en") -> dict[str, Any]:
    """Generate safe, standardized refusal payload for prompt injection attempts.

    Args:
        lang: Language preference ('en' or 'hi').

    Returns:
        Dictionary conforming to standard AI assistant response schema.
    """
    if lang == "hi":
        return {
            "summary": "सुरक्षा कारणों से इस अनुरोध को अस्वीकार कर दिया गया है।",
            "tips": ["कृपया केवल वायु गुणवत्ता और स्वास्थ्य सुरक्षा से संबंधित प्रश्न पूछें।"],
            "answer": "मैं उन निर्देशों को पूरा नहीं कर सकता जो सुरक्षा दिशानिर्देशों को बदलने का प्रयास करते हैं।",
        }
    return {
        "summary": "Request blocked for security reasons.",
        "tips": ["Please ask only about air quality planning and household exposures."],
        "answer": "Cannot fulfill requests that attempt to alter core safety instructions.",
    }
