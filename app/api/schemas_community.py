"""Community pledge, AI assistant, and error envelope schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PledgeRequest(BaseModel):
    """Community action pledge submission."""

    model_config = ConfigDict(extra="forbid")

    area_code: str = Field(
        pattern=r"^[A-Z0-9-]{3,10}$",
        description="Coarse geographic district code (e.g. DL-01)",
    )
    action: str = Field(min_length=2, max_length=50, description="Pledged action identifier")
    count: int = Field(default=1, ge=1, le=1000, description="Number of instances or days")


class PledgeResponse(BaseModel):
    """Pledge submission status confirmation."""

    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    area_code: str


class AskRequest(BaseModel):
    """User inquiry submission for AI assistant guidance."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=300, description="User question text")
    facts: dict[str, Any] = Field(default_factory=dict, description="Ground truth facts")
    language: Literal["en", "hi"] = Field(default="en", description="Target language")


class AskResponse(BaseModel):
    """Assistant guidance response with safe substituted placeholders."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    tips: list[str]
    answer: str
    is_red_flag: bool = Field(default=False, description="Whether inquiry triggered medical triage")
    red_flag: dict[str, Any] | None = Field(
        default=None,
        description="Optional clinical emergency triage details",
    )


class ErrorEnvelope(BaseModel):
    """Standardized error envelope returning error message and tracking id."""

    model_config = ConfigDict(extra="forbid")

    error: str
    correlation_id: str
