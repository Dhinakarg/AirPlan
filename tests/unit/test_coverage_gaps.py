"""Targeted tests closing remaining branch and error-handler coverage gaps."""

import json
from http import HTTPStatus
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from app.ai.guards import looks_like_injection, sanitize_user_text
from app.ai.provider import GeminiProvider, TemplateProvider, get_assistant_provider
from app.ai.validator import validate_assistant_output
from app.api.middleware import RateLimiter
from app.api.schemas import HomeAnalyzeRequest
from app.api.schemas_community import AskRequest
from app.config import Settings
from app.data.air_client import (
    _fetch_with_lifecycle,
    load_sample_air_data,
    load_scenario_air_data,
)
from app.engine.models import HouseholdContext
from app.errors import AIError, AirDataError, AirPlanError, NotFoundError
from app.main import _format_validation_msg, app
from app.services.assistant_service import generate_clean_air_advice
from app.services.plan_service import MemberPlanInput, _resolve_context


def test_main_error_handlers_and_root_html(client: TestClient) -> None:
    """Verify domain_error_handler, http_error_handler, validation helpers, and HTML root."""
    assert _format_validation_msg([]) == "Invalid request payload or parameters."
    assert _format_validation_msg([{"loc": (), "msg": "bad"}]) == "Validation failed: bad"

    @app.get("/_test_domain_err")
    def _raise_domain() -> None:
        raise AirPlanError("domain failure")

    @app.get("/_test_not_found")
    def _raise_not_found() -> None:
        raise NotFoundError("item missing")

    res_dom = client.get("/_test_domain_err")
    assert res_dom.status_code == HTTPStatus.BAD_REQUEST
    assert res_dom.json()["error"] == "domain failure"

    res_nf = client.get("/_test_not_found")
    assert res_nf.status_code == HTTPStatus.NOT_FOUND
    assert res_nf.json()["error"] == "item missing"

    res_404 = client.get("/api/v1/does-not-exist")
    assert res_404.status_code == HTTPStatus.NOT_FOUND
    assert "correlation_id" in res_404.json()

    res_html = client.get("/", headers={"Accept": "text/html"})
    assert res_html.status_code == HTTPStatus.OK
    assert "text/html" in res_html.headers["content-type"]


def test_middleware_invalid_content_length_and_rate_limiter_eviction(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify non-numeric Content-Length is ignored and RateLimiter bounds memory."""
    res = client.post(
        "/api/v1/home/analyze",
        json={},
        headers={"Content-Length": "not-a-number"},
    )
    assert res.status_code == HTTPStatus.OK

    now = [100.0]
    monkeypatch.setattr("app.api.middleware.time.monotonic", lambda: now[0])
    limiter = RateLimiter(window_seconds=10.0, max_clients=2)
    assert limiter.is_allowed("10.0.0.1", 5) is True
    assert limiter.is_allowed("10.0.0.2", 5) is True
    # Active capacity reached -> evicts oldest key when neither is expired
    assert limiter.is_allowed("10.0.0.3", 5) is True
    assert len(limiter.timestamps) == 2
    assert "10.0.0.1" not in limiter.timestamps

    # Advance past window so remaining keys expire and get pruned cleanly
    now[0] = 120.0
    assert limiter.is_allowed("10.0.0.4", 5) is True
    assert list(limiter.timestamps.keys()) == ["10.0.0.4"]


def test_schema_bounds_for_ask_facts_and_indoor_pm25() -> None:
    """Verify AskRequest.facts bounds and indoor_pm25_reading ceiling."""
    with pytest.raises(ValidationError, match="32 keys"):
        AskRequest(question="hi", facts={f"k{i}": i for i in range(33)})
    with pytest.raises(ValidationError, match="64 characters"):
        AskRequest(question="hi", facts={"x" * 65: 1})
    with pytest.raises(ValidationError, match="Nested objects"):
        AskRequest(question="hi", facts={"nested": {"a": 1}})
    with pytest.raises(ValidationError, match="300 characters"):
        AskRequest(question="hi", facts={"long": "a" * 301})
    with pytest.raises(ValidationError, match="20 items"):
        AskRequest(question="hi", facts={"items": list(range(21))})
    with pytest.raises(ValidationError, match="Invalid list item"):
        AskRequest(question="hi", facts={"items": [None]})
    with pytest.raises(ValidationError, match="Unsupported type"):
        AskRequest(question="hi", facts={"bad": object()})
    with pytest.raises(ValidationError):
        HomeAnalyzeRequest(indoor_pm25_reading=5000.1)


def test_air_client_error_branches_and_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify sample/scenario I/O failures, unknown scenario, and owned client close."""
    with pytest.raises(AirDataError, match="Unknown air scenario"):
        load_scenario_air_data("invalid_scenario")

    def _boom(*_args: object, **_kwargs: object) -> list[object]:
        raise OSError("disk read failed")

    monkeypatch.setattr("app.data.air_client._load_hourly_file", _boom)
    with pytest.raises(AirDataError, match="Failed loading sample"):
        load_sample_air_data()
    with pytest.raises(AirDataError, match="Failed loading scenario"):
        load_scenario_air_data("severe")

    fake_http = MagicMock(spec=httpx.Client)
    monkeypatch.setattr("app.data.air_client._try_fetch_remote", lambda *_a: [])
    _fetch_with_lifecycle(fake_http, 28.61, 77.21, "2026-01-01", should_close=True)
    fake_http.close.assert_called_once()


def test_ai_and_service_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AI guards, validator edge cases, provider close, and explicit context."""
    assert sanitize_user_text("") == ""
    assert looks_like_injection("") is False
    assert validate_assistant_output("   ") is None
    assert validate_assistant_output("{bad json") is None

    monkeypatch.setattr(
        "app.ai.provider.get_settings",
        lambda: Settings(ai_provider="gemini", gemini_api_key="k"),
    )

    def _raise_init(*_a: object, **_kw: object) -> None:
        raise AIError("init failed")

    monkeypatch.setattr("app.ai.provider.GeminiProvider", _raise_init)
    assert isinstance(get_assistant_provider(), TemplateProvider)

    fake_resp = MagicMock()
    fake_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"summary":"s","tips":[],"answer":"a"}'}]}}]
    }
    fake_client = MagicMock(spec=httpx.Client)
    fake_client.post.return_value = fake_resp
    monkeypatch.setattr("app.ai.provider.httpx.Client", lambda **_kw: fake_client)
    gp = GeminiProvider(api_key="k")
    assert "summary" in gp.generate("hi")
    fake_client.close.assert_called_once()

    class ValidProvider:
        def generate(self, _prompt: str) -> str:
            return json.dumps(
                {
                    "summary": "Index {{index_after}}.",
                    "tips": ["Keep windows shut."],
                    "answer": "Saved {{dose_saved}}.",
                }
            )

    res = generate_clean_air_advice(
        "How is today?",
        {"index_after": 42, "dose_saved": 120},
        provider=ValidProvider(),
    )
    assert "42" in res["summary"]

    explicit = HouseholdContext(has_asthma_or_heart=True, has_children=False)
    assert _resolve_context(explicit, [MemberPlanInput("A")]) is explicit
    assert Path("static/index.html").exists()

