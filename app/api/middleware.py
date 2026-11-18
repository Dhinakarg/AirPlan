"""Security headers, correlation tracking, sliding-window rate limiting, and size guards."""

import time
import uuid
from collections import defaultdict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings

MAX_REQUEST_SIZE_BYTES: int = 100_000  # 100 KB maximum payload
RATE_LIMIT_WINDOW_SECONDS: float = 60.0

_IP_REQUEST_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)


def reset_rate_limiter() -> None:
    """Clear in-memory IP timestamp records (useful for test isolation)."""
    _IP_REQUEST_TIMESTAMPS.clear()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Unified security middleware enforcing headers, rate limiting, and request limits."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process incoming request through security policies and attach tracking headers.

        Args:
            request: Incoming HTTP request.
            call_next: Next request processing callable.

        Returns:
            HTTP response with security headers and correlation ID.
        """
        # 1. Correlation tracking
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = corr_id

        # 2. Request body size limit
        content_length = request.headers.get("Content-Length")
        if content_length:
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

        # 3. Per-IP sliding-window rate limiting
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        limit = get_settings().rate_limit_per_minute

        # Prune records older than the sliding window
        timestamps = [
            t for t in _IP_REQUEST_TIMESTAMPS[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS
        ]
        if len(timestamps) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded. Please retry later.",
                    "correlation_id": corr_id,
                },
                headers={
                    "Retry-After": "60",
                    "X-Correlation-ID": corr_id,
                },
            )

        timestamps.append(now)
        _IP_REQUEST_TIMESTAMPS[client_ip] = timestamps

        # 4. Invoke route handler
        response = await call_next(request)

        # 5. Attach security headers and correlation tracking
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-eval' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; "
            "object-src 'none'; base-uri 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        return response
