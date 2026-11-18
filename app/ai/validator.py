"""Output schema validation, anti-hallucination digit guards, and placeholder substitution."""

import json
import re
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ALLOWED_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {
        "index_after",
        "index_before",
        "dose_saved",
        "window_start",
        "window_end",
        "mean_pm25",
        "top_intervention",
        "cleanest_hour",
        "stagnation_hours",
    }
)

URL_REGEX: Final[re.Pattern[str]] = re.compile(r"https?://|www\.", re.IGNORECASE)
MARKUP_REGEX: Final[re.Pattern[str]] = re.compile(r"<[^>]+>")
PLACEHOLDER_REGEX: Final[re.Pattern[str]] = re.compile(r"\{\{([^}]+)\}\}")
DIGIT_REGEX: Final[re.Pattern[str]] = re.compile(r"\d")


class AssistantPayload(BaseModel):
    """Rigid structural payload for LLM responses."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="High-level plan summary with strict placeholders")
    tips: list[str] = Field(description="Actionable household tips with strict placeholders")
    answer: str = Field(description="Direct question response with strict placeholders")


def _is_text_safe(text: str) -> bool:
    """Validate that text contains no URLs, markup, unknown placeholders, or naked digits."""
    if URL_REGEX.search(text) or MARKUP_REGEX.search(text):
        return False

    placeholders = PLACEHOLDER_REGEX.findall(text)
    for p in placeholders:
        if p.strip() not in ALLOWED_PLACEHOLDERS:
            return False

    # Strip valid placeholders and check for any remaining digits
    text_without_placeholders = PLACEHOLDER_REGEX.sub("", text)
    return not bool(DIGIT_REGEX.search(text_without_placeholders))


def validate_assistant_output(raw_output: str) -> AssistantPayload | None:
    """Validate LLM output against rigid schema, placeholder, and anti-hallucination rules.

    Rejects any output containing:
    - Digits outside of allowed {{placeholder}} tags
    - Unknown placeholder names
    - URLs or domain links
    - Markup / HTML / XML tags

    Args:
        raw_output: Raw text string received from the LLM provider.

    Returns:
        AssistantPayload instance if valid, or None if rejected.
    """
    if not raw_output or not raw_output.strip():
        return None

    try:
        data = json.loads(raw_output.strip())
        payload = AssistantPayload.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None

    if not _is_text_safe(payload.summary):
        return None
    if not _is_text_safe(payload.answer):
        return None
    for tip in payload.tips:
        if not _is_text_safe(tip):
            return None

    return payload


def _replace_placeholders(text: str, values: dict[str, Any]) -> str:
    """Replace all {{key}} tags in text with provided dictionary values."""

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        val = values.get(key)
        return str(val) if val is not None else match.group(0)

    return PLACEHOLDER_REGEX.sub(_sub, text)


def substitute_payload(
    payload: AssistantPayload,
    values: dict[str, Any],
) -> dict[str, Any]:
    """Substitute placeholders in validated payload using verified engine facts.

    Args:
        payload: Validated AssistantPayload with placeholders.
        values: Ground-truth domain dictionary from calculation engine.

    Returns:
        JSON-serializable dictionary with substituted facts.
    """
    return {
        "summary": _replace_placeholders(payload.summary, values),
        "tips": [_replace_placeholders(t, values) for t in payload.tips],
        "answer": _replace_placeholders(payload.answer, values),
    }
