"""Provider protocol and client implementations for clean-air assistance."""

import logging
from typing import Any, Final, Protocol

import httpx

from app.ai.fallback import get_fallback_json
from app.config import get_settings
from app.errors import AIError

logger = logging.getLogger(__name__)


class GenAIAPIError(Exception):
    """Exception class representing Google GenAI SDK errors."""

    def __init__(
        self,
        code: int = 500,
        response_json: object = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialize error with status code and response JSON."""
        super().__init__(f"APIError {code}: {response_json}")
        self.code = code
        self.response_json = response_json


__all__ = [
    "AssistantProvider",
    "GeminiProvider",
    "GenAIAPIError",
    "TemplateProvider",
    "get_assistant_provider",
]

GEMINI_API_URL: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
)
GEMINI_TIMEOUT_SECONDS: Final[float] = 10.0


class AssistantProvider(Protocol):
    """Protocol defining generative or template-based assistant interfaces."""

    def generate(self, prompt: str) -> str:
        """Generate response text for the provided input prompt.

        Args:
            prompt: Structured prompt including system constraints and data.

        Returns:
            JSON-formatted string matching the AssistantPayload schema.
        """
        ...


class TemplateProvider:
    """Offline deterministic response generator that never hallucinates facts."""

    def generate(self, prompt: str) -> str:
        """Produce safe template response with authorized placeholders.

        Args:
            prompt: Input prompt string.

        Returns:
            JSON string containing safe standard template.
        """
        lang = "hi" if "Respond in Hindi" in prompt else "en"
        return get_fallback_json(lang)


class GeminiProvider:
    """Remote Gemini API integration with timeout and error handling."""

    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None) -> None:
        """Initialize GeminiProvider with validated credentials.

        Args:
            api_key: Optional Gemini API key (defaults to config setting).
            client: Optional pre-configured httpx.Client.
        """
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise AIError("Gemini API key is missing or unconfigured.")
        self._client = client

    @staticmethod
    def _extract_candidate_text(data: dict[str, Any]) -> str:
        """Extract first candidate part text from Gemini response body."""
        candidates = data.get("candidates", [])
        if not candidates:
            raise AIError("Gemini returned empty candidates list.")
        return str(candidates[0]["content"]["parts"][0]["text"])

    def generate(self, prompt: str) -> str:
        """Execute remote generation request against Gemini endpoints."""
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        http = self._client or httpx.Client(timeout=GEMINI_TIMEOUT_SECONDS)
        try:
            resp = http.post(GEMINI_API_URL, params=params, json=payload)
            resp.raise_for_status()
            return self._extract_candidate_text(resp.json())
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.HTTPStatusError,
            httpx.HTTPError,
            GenAIAPIError,
        ) as exc:
            raise AIError(f"Gemini API generation failed: {exc}") from exc
        finally:
            if self._client is None:
                http.close()


def get_assistant_provider() -> AssistantProvider:
    """Instantiate appropriate assistant provider based on environment configuration.

    If AI_PROVIDER is 'gemini' and an API key is present, returns GeminiProvider.
    Otherwise, gracefully returns TemplateProvider for offline operation.

    Returns:
        Instance conforming to AssistantProvider protocol.
    """
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        try:
            return GeminiProvider(settings.gemini_api_key)
        except AIError:
            logger.warning("Failed to initialize GeminiProvider; falling back to TemplateProvider.")
            return TemplateProvider()
    return TemplateProvider()
