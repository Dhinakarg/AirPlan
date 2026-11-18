"""Domain exception hierarchy for AirLedger."""

from typing import Any


class AirLedgerError(Exception):
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


class ValidationError(AirLedgerError):
    """Raised when data fails domain validation rules."""


class SimulationError(AirLedgerError):
    """Raised when aerosol or exposure calculation fails."""


class AirDataError(AirLedgerError):
    """Raised when air quality data fetching or parsing fails."""


class AIError(AirLedgerError):
    """Raised when GenAI response generation or validation fails."""


class NotFoundError(AirLedgerError):
    """Raised when a requested resource is not found."""
