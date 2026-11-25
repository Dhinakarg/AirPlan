"""GenAI assistant dialogue and plain-language explanation service."""

import logging
from typing import Any

from app.ai.fallback import get_fallback_payload
from app.ai.guards import (
    build_injection_refusal,
    looks_like_injection,
    sanitize_user_text,
)
from app.ai.prompts import format_user_prompt
from app.ai.provider import AssistantProvider, GenAIAPIError, get_assistant_provider
from app.ai.validator import (
    AssistantPayload,
    substitute_payload,
    validate_assistant_output,
)
from app.engine.models import RedFlag
from app.engine.safety_rules import detect_red_flags
from app.errors import AIError

logger = logging.getLogger(__name__)


def _try_generate_and_validate(p: AssistantProvider, prompt: str) -> AssistantPayload | None:
    """Attempt remote AI generation and syntactic anti-hallucination validation."""
    try:
        raw_output = p.generate(prompt)
        payload = validate_assistant_output(raw_output)
        if payload is None:
            logger.info("Provider output failed validation; falling back to template.")
        return payload
    except (AIError, GenAIAPIError, RuntimeError, ValueError, KeyError, TimeoutError) as exc:
        logger.warning("Provider call failed (%s); using fallback template.", exc)
        return None


def generate_clean_air_advice(
    question: str,
    facts: dict[str, Any],
    lang: str = "en",
    provider: AssistantProvider | None = None,
) -> dict[str, Any]:
    """Generate safe, validated clean-air advice with grounded placeholder substitution."""
    if looks_like_injection(question):
        logger.warning("Prompt injection pattern detected in user query.")
        return build_injection_refusal(lang)

    safe_question = sanitize_user_text(question)
    p = provider or get_assistant_provider()
    prompt = format_user_prompt(safe_question, facts, lang)

    payload = _try_generate_and_validate(p, prompt)
    if payload is None:
        payload = get_fallback_payload(lang)
    return substitute_payload(payload, facts)


def _build_red_flag_response(red_flag: RedFlag) -> dict[str, Any]:
    """Construct medical emergency override payload."""
    return {
        "is_red_flag": True,
        "red_flag": red_flag.model_dump(),
        "summary": "MEDICAL EMERGENCY: Immediate clinical attention required.",
        "tips": [
            "Do not wait for air quality changes or ambient improvements.",
            "Call emergency medical services immediately or visit emergency room.",
        ],
        "answer": (
            f"CRITICAL: {red_flag.action.upper()}. "
            f"Detected symptom: '{red_flag.symptom}'. "
            "This directive strictly overrides all air quality guidance."
        ),
    }


def ask_assistant(
    question: str,
    facts: dict[str, Any] | None = None,
    lang: str = "en",
    provider: AssistantProvider | None = None,
) -> dict[str, Any]:
    """Process user query through clinical red-flag triage, injection guards, and AI."""
    red_flag = detect_red_flags(question)
    if red_flag is not None:
        return _build_red_flag_response(red_flag)
    return generate_clean_air_advice(question, facts or {}, lang=lang, provider=provider)
