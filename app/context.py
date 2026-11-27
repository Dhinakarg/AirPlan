"""Request-scoped correlation ID context for structured logging."""

from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    """Return the active request correlation ID or '-' outside a request."""
    return correlation_id_var.get()

