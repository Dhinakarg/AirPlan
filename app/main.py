"""FastAPI application entrypoint for AirLedger."""

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    """Operational healthcheck endpoint.

    Returns:
        Dictionary with status and application identifier.
    """
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def root() -> Any:
    """Service root endpoint.

    Returns:
        JSON status message.
    """
    return JSONResponse(content={"status": "ok", "app": settings.app_name})
