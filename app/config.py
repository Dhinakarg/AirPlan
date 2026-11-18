"""Application configuration and validated runtime settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="AirPlan", description="Service identifier")
    environment: str = Field(default="development", description="Runtime environment")
    host: str = Field(default="127.0.0.1", description="Bind host address")
    port: int = Field(default=8000, description="Bind port number")
    ai_provider: str = Field(default="template", description="AI provider (template|gemini)")
    gemini_api_key: str | None = Field(default=None, description="Optional Gemini API key")
    air_data_mode: str = Field(default="sample", description="Air data mode (live|sample)")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    cors_origins: str = Field(default="*", description="Allowed CORS origins")


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached singleton application runtime settings."""
    return Settings()


settings = get_settings()
