"""GenAI assistant dialogue and plain-language explanation service."""

import logging
from typing import Any

from app.ai.fallback import get_fallback_payload
from app.ai.guards import build_injection_refusal, looks_like_injection, sanitize_user_text
from app.ai.prompts import format_user_prompt
from app.ai.provider import AssistantProvider, get_assistant_provider
from app.ai.validator import substitute_payload, validate_assistant_output
from app.errors import AIError

logger = logging.getLogger(__name__)


def generate_clean_air_advice(
    question: str,
    facts: dict[str, Any],
    lang: str = "en",
    provider: AssistantProvider | None = None,
) -> dict[str, Any]:
    """Generate safe, validated clean-air advice with grounded placeholder substitution.

    Guarantees:
    - Injected queries are blocked immediately with a refusal payload.
    - Raw output is strictly validated against digit anti-hallucination and markup rules.
    - Any validation rejection or provider failure transparently falls back to safe templates.
    - Output values are strictly populated from ground-truth engine calculation facts.

    Args:
        question: User inquiry text.
        facts: Ground-truth calculation parameters and domain facts.
        lang: User interface language code ('en' or 'hi').
        provider: Optional explicit AssistantProvider instance.

    Returns:
        Substituted JSON-serializable dictionary with summary, tips, and answer.
    """
    if looks_like_injection(question):
        logger.warning("Prompt injection pattern detected in user query.")
        return build_injection_refusal(lang)

    safe_question = sanitize_user_text(question)
    p = provider or get_assistant_provider()
    prompt = format_user_prompt(safe_question, facts, lang)

    payload = None
    try:
        raw_output = p.generate(prompt)
        payload = validate_assistant_output(raw_output)
        if payload is None:
            logger.info("Provider output failed validation; falling back to template.")
    except (AIError, Exception) as exc:
        logger.warning("Provider call failed (%s); using fallback template.", exc)

    if payload is None:
        payload = get_fallback_payload(lang)

    return substitute_payload(payload, facts)
