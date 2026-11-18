"""Common dependency injection providers for API endpoints."""

from app.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Provide application configuration settings dependency."""
    return get_settings()
