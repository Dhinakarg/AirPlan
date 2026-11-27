"""Community pledge, AI assistant, and error envelope schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


_MAX_FACTS_KEYS = 32
_MAX_FACT_KEY_LEN = 64
_MAX_FACT_STR_LEN = 300
_MAX_FACT_LIST_LEN = 20


def _validate_fact_primitive(val: object, key: str) -> None:
    """Validate a scalar fact value is a bounded primitive."""
    if isinstance(val, str):
        if len(val) > _MAX_FACT_STR_LEN:
            raise ValueError(f"facts['{key}'] exceeds {_MAX_FACT_STR_LEN} characters")
        return
    if not isinstance(val, int | float | bool | type(None)):
        raise ValueError(f"Unsupported type in facts['{key}']")


def _validate_fact_value(val: object, key: str) -> None:
    """Validate a single fact value is a bounded primitive or short primitive list."""
    if isinstance(val, dict):
        raise ValueError(f"Nested objects are not allowed in facts['{key}']")
    if isinstance(val, list):
        if len(val) > _MAX_FACT_LIST_LEN:
            raise ValueError(f"facts['{key}'] list exceeds {_MAX_FACT_LIST_LEN} items")
        for item in val:
            if item is None:
                raise ValueError(f"Invalid list item in facts['{key}']")
            _validate_fact_primitive(item, key)
        return
    _validate_fact_primitive(val, key)


class AskRequest(BaseModel):
    """User inquiry submission for AI assistant guidance."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=300, description="User question text")
    facts: dict[str, Any] = Field(default_factory=dict, description="Ground truth facts")
    language: Literal["en", "hi"] = Field(default="en", description="Target language")

    @field_validator("facts")
    @classmethod
    def validate_facts_bounds(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Enforce key count, key length, flatness, and string length limits on facts."""
        if len(value) > _MAX_FACTS_KEYS:
            raise ValueError(f"facts cannot exceed {_MAX_FACTS_KEYS} keys")
        for k, v in value.items():
            if len(k) > _MAX_FACT_KEY_LEN:
                raise ValueError(f"facts key '{k[:16]}...' exceeds {_MAX_FACT_KEY_LEN} characters")
            _validate_fact_value(v, k)
        return value


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
