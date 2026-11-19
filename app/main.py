"""FastAPI application entrypoint for AirPlan."""

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import SecurityMiddleware
from app.api.routes import router as api_router
from app.config import get_settings
from app.errors import AirPlanError, NotFoundError

logger = logging.getLogger("airplan")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration derived strictly from validated application settings
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified security middleware (correlation ID, rate limiting, payload ceiling, security headers)
app.add_middleware(SecurityMiddleware)

# API routes
app.include_router(api_router)

# Static file serving
static_path = Path(__file__).resolve().parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.exception_handler(AirPlanError)
async def domain_error_handler(request: Request, exc: AirPlanError) -> JSONResponse:
    """Handle domain exceptions with sanitized error payloads.

    Args:
        request: Incoming HTTP request.
        exc: Domain error instance.

    Returns:
        JSONResponse with generic error message and correlation ID.
    """
    corr_id = getattr(request.state, "correlation_id", "unknown")
    status = 404 if isinstance(exc, NotFoundError) else 400
    return JSONResponse(
        status_code=status,
        content={"error": exc.message, "correlation_id": corr_id},
        headers={"X-Correlation-ID": corr_id},
    )


def _extract_field_path(loc: Sequence[object]) -> str:
    """Format property hierarchy excluding root payload wrapper."""
    return " -> ".join(str(item) for item in loc if item != "body")


def _format_validation_msg(errors: Sequence[Mapping[str, object] | object]) -> str:
    """Format the first validation error message without leaking internal trace details."""
    if not errors or not isinstance(errors[0], dict):
        return "Invalid request payload or parameters."
    field = _extract_field_path(errors[0].get("loc", []))
    msg = errors[0].get("msg", "Invalid value")
    if field:
        return f"Validation failed at '{field}': {msg}"
    return f"Validation failed: {msg}"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request payload validation failures without leaking stack traces."""
    corr_id = getattr(request.state, "correlation_id", "unknown")
    error_msg = _format_validation_msg(exc.errors())
    return JSONResponse(
        status_code=422,
        content={"error": error_msg, "correlation_id": corr_id},
        headers={"X-Correlation-ID": corr_id},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP errors with correlation tracking.

    Args:
        request: Incoming HTTP request.
        exc: Starlette HTTP exception.

    Returns:
        JSONResponse with appropriate status and correlation ID.
    """
    corr_id = getattr(request.state, "correlation_id", "unknown")
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": detail, "correlation_id": corr_id},
        headers={"X-Correlation-ID": corr_id},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler returning generic message without traces.

    Args:
        request: Incoming HTTP request.
        exc: Unhandled exception.

    Returns:
        JSONResponse with 500 status and tracking ID.
    """
    corr_id = getattr(request.state, "correlation_id", "unknown")
    logger.error("Unhandled error [correlation_id=%s]: %s", corr_id, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred.", "correlation_id": corr_id},
        headers={"X-Correlation-ID": corr_id},
    )


@app.get("/health")
@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """Operational healthcheck endpoint.

    Returns:
        Dictionary with status and application identifier.
    """
    return {"status": "ok", "app": settings.app_name}


@app.get("/", response_model=None)
def root(request: Request) -> Response | dict[str, str]:
    """Root endpoint providing service status information or web UI.

    Args:
        request: Incoming HTTP request.

    Returns:
        FileResponse if browser requested HTML, else JSON status dictionary.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*"):
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    return {"status": "ok", "app": settings.app_name}
