"""Domain exception hierarchy for AirPlan."""

from typing import Any


class AirPlanError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize domain error.

        Args:
            message: Human-readable error message.
            details: Optional error context dictionary.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AirPlanError):
    """Raised when data fails domain validation rules."""


class SimulationError(AirPlanError):
    """Raised when aerosol or exposure calculation fails."""


class AirDataError(AirPlanError):
    """Raised when air quality data fetching or parsing fails."""


class AIError(AirPlanError):
    """Raised when GenAI response generation or validation fails."""


class NotFoundError(AirPlanError):
    """Raised when a requested resource is not found."""
