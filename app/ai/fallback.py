"""Deterministic template-based explanation generator for offline execution."""

import json

from app.ai.validator import AssistantPayload

FALLBACK_TEMPLATES: dict[str, dict[str, object]] = {
    "en": {
        "summary": (
            "Your optimized daily routine lowers household exposure to index "
            "{{index_after}} (saving {{dose_saved}} ug of inhaled PM2.5 particulate mass)."
        ),
        "tips": [
            "Shift exercise to the clean-air window starting at hour {{window_start}}.",
            "Keep residential windows sealed during nocturnal smog and morning peak inversions.",
            "Adopt damp wet mopping instead of dry sweeping to halt surface dust resuspension.",
        ],
        "answer": (
            "Based on your profile, synchronizing outdoor transit with hour {{window_start}} "
            "and deploying recommended interventions reduces your inhaled dose by "
            "{{dose_saved}} ug."
        ),
    },
    "hi": {
        "summary": (
            "आपकी अनुकूलित दिनचर्या जोखिम सूचकांक को {{index_after}} तक घटाती है "
            "(कुल {{dose_saved}} माइक्रोग्राम PM2.5 की बचत)।"
        ),
        "tips": [
            "व्यायाम और भारी गतिविधियों को समय {{window_start}} पर स्थानांतरित करें।",
            "सुबह और रात की तेज धुंध के दौरान खिड़कियां और दरवाजे पूरी तरह बंद रखें।",
            "धूल को हवा में उड़ने से रोकने के लिए सूखे झाड़ू के स्थान पर गीले पोंछे का प्रयोग करें।",
        ],
        "answer": (
            "आपके घरेलू विवरण और वायु गुणवत्ता पूर्वानुमान के अनुसार, समय {{window_start}} "
            "का उपयोग करने से आपकी सांस में जाने वाला प्रदूषण {{dose_saved}} माइक्रोग्राम कम होता है।"
        ),
    },
}


def get_fallback_payload(lang: str = "en") -> AssistantPayload:
    """Retrieve validated deterministic fallback response payload.

    Args:
        lang: Target language code ('en' or 'hi').

    Returns:
        AssistantPayload populated with standard safe placeholders.
    """
    tmpl = FALLBACK_TEMPLATES.get(lang, FALLBACK_TEMPLATES["en"])
    return AssistantPayload.model_validate(tmpl)


def get_fallback_json(lang: str = "en") -> str:
    """Retrieve raw JSON string of the deterministic fallback response.

    Args:
        lang: Target language code ('en' or 'hi').

    Returns:
        JSON string representation.
    """
    payload = get_fallback_payload(lang)
    return json.dumps(payload.model_dump())
