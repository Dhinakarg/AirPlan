"""Security, rate limiting, and request tracking middleware."""

import time
import uuid
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.config import get_settings
from app.constants import MAX_REQUEST_SIZE_BYTES, RATE_LIMIT_WINDOW_SECONDS


# In-memory sliding-window request timestamps keyed by client IP
class RateLimiter:
    """Sliding-window IP rate limiter with injectable state."""

    def __init__(self, window_seconds: float = RATE_LIMIT_WINDOW_SECONDS) -> None:
        """Initialize RateLimiter with sliding-window duration."""
        self.window_seconds = window_seconds
        self.timestamps: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str, limit: int) -> bool:
        """Check whether client request is within sliding-window quota."""
        now = time.monotonic()
        recent = [t for t in self.timestamps[client_ip] if now - t < self.window_seconds]
        if len(recent) >= limit:
            self.timestamps[client_ip] = recent
            return False
        recent.append(now)
        self.timestamps[client_ip] = recent
        return True

    def clear(self) -> None:
        """Purge all recorded client IP timestamps."""
        self.timestamps.clear()


_DEFAULT_RATE_LIMITER = RateLimiter()

__all__ = [
    "CSP_HEADER_VALUE",
    "MAX_REQUEST_SIZE_BYTES",
    "RateLimiter",
    "SecurityMiddleware",
    "clear_rate_limit_cache",
    "reset_rate_limiter",
]

CSP_HEADER_VALUE = (
    "default-src 'self'; script-src 'self' 'unsafe-eval' https://cdnjs.cloudflare.com; "
    "connect-src 'self' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; "
    "object-src 'none'; base-uri 'self'"
)


def clear_rate_limit_cache() -> None:
    """Clear in-memory IP timestamp records (useful for test isolation)."""
    _DEFAULT_RATE_LIMITER.clear()


# Backward-compatible alias for test harness
reset_rate_limiter = clear_rate_limit_cache


class SecurityMiddleware(BaseHTTPMiddleware):
    """Unified security middleware enforcing headers, rate limiting, and request limits."""

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize SecurityMiddleware with optional injected RateLimiter."""
        super().__init__(app)
        self.rate_limiter = rate_limiter or _DEFAULT_RATE_LIMITER

    @staticmethod
    def _extract_correlation_id(request: Request) -> str:
        """Extract or generate unique correlation ID for tracking."""
        return request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    @staticmethod
    def _check_payload_size(request: Request, corr_id: str) -> Response | None:
        """Validate that incoming Content-Length does not exceed maximum ceiling."""
        content_length = request.headers.get("Content-Length")
        if not content_length:
            return None
        try:
            if int(content_length) > MAX_REQUEST_SIZE_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Payload exceeds maximum allowed size of 100 KB.",
                        "correlation_id": corr_id,
                    },
                    headers={"X-Correlation-ID": corr_id},
                )
        except ValueError:
            pass
        return None

    @staticmethod
    def _resolve_client_ip(request: Request) -> str:
        """Resolve client IP strictly adhering to TRUSTED_PROXY configuration."""
        if get_settings().trusted_proxy:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    def _check_rate_limit(self, request: Request, corr_id: str) -> Response | None:
        """Enforce per-IP sliding-window request throttling."""
        client_ip = self._resolve_client_ip(request)
        limit = get_settings().rate_limit_per_minute

        if not self.rate_limiter.is_allowed(client_ip, limit):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded. Please retry later.",
                    "correlation_id": corr_id,
                },
                headers={"Retry-After": "60", "X-Correlation-ID": corr_id},
            )
        return None

    @staticmethod
    def _attach_security_headers(request: Request, response: Response, corr_id: str) -> None:
        """Apply strict security and privacy headers to all outgoing responses."""
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["Content-Security-Policy"] = CSP_HEADER_VALUE
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process incoming request through security policies and attach tracking headers."""
        corr_id = self._extract_correlation_id(request)
        request.state.correlation_id = corr_id

        size_error = self._check_payload_size(request, corr_id)
        if size_error is not None:
            self._attach_security_headers(request, size_error, corr_id)
            return size_error

        rate_error = self._check_rate_limit(request, corr_id)
        if rate_error is not None:
            self._attach_security_headers(request, rate_error, corr_id)
            return rate_error

        response = await call_next(request)
        self._attach_security_headers(request, response, corr_id)
        return response
