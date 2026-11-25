"""API security, headers, rate limiting, and request tracking test suite."""

import logging
from http import HTTPStatus
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.api.middleware import MAX_REQUEST_SIZE_BYTES, reset_rate_limiter
from app.main import app


def test_security_headers_present_on_all_responses(client: TestClient) -> None:
    """Verify presence of security headers on responses."""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    headers = response.headers

    expected_exact = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    }
    for header, expected_val in expected_exact.items():
        assert headers.get(header) == expected_val

    assert "X-Correlation-ID" in headers
    assert "Content-Security-Policy" in headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Permissions-Policy" in headers


def test_correlation_id_generated_and_returned(client: TestClient) -> None:
    """Verify automatic generation of correlation ID when omitted by client."""
    response = client.get("/health")
    corr_id = response.headers.get("X-Correlation-ID")
    assert corr_id is not None
    assert len(corr_id) > 10


def test_correlation_id_preserved_when_passed(client: TestClient) -> None:
    """Verify correlation ID provided in request header is propagated to response."""
    custom_id = "test-corr-trace-999"
    response = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response.headers.get("X-Correlation-ID") == custom_id


def test_rate_limit_exceeded_returns_429(client: TestClient) -> None:
    """Verify sliding-window rate limiting triggers 429 with Retry-After header."""
    reset_rate_limiter()
    with patch("app.api.middleware.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_per_minute = 3

        for _ in range(3):
            res = client.get("/health")
            assert res.status_code == HTTPStatus.OK

        res_blocked = client.get("/health")
        assert res_blocked.status_code == HTTPStatus.TOO_MANY_REQUESTS
        assert res_blocked.headers.get("Retry-After") == "60"
        data = res_blocked.json()
        assert "Rate limit exceeded" in data["error"]
        assert "correlation_id" in data


def test_payload_too_large_returns_413(client: TestClient) -> None:
    """Verify oversized request payload (> 100 KB) triggers 413 error."""
    oversize = str(MAX_REQUEST_SIZE_BYTES + 500)
    response = client.post(
        "/api/v1/ask",
        headers={"Content-Length": oversize},
        json={"question": "Test?"},
    )
    assert response.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    data = response.json()
    assert "100 KB" in data["error"]
    assert "correlation_id" in data


def test_global_exception_handler_returns_generic_error() -> None:
    """Verify unhandled exceptions return generic JSON without internal stack traces."""
    error_client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "app.api.routes.ask_assistant",
        side_effect=RuntimeError("Secret DB"),
    ):
        response = error_client.post(
            "/api/v1/ask",
            json={"question": "Trigger error?", "facts": {}},
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert "correlation_id" in data
        assert "Secret DB" not in data["error"]
        assert "RuntimeError" not in data["error"]


def test_static_files_served(client: TestClient) -> None:
    """Verify static assets are properly served under /static."""
    css_names = (
        "tokens.css",
        "base.css",
        "layout.css",
        "nav.css",
        "buttons.css",
        "cards.css",
        "forms.css",
        "results.css",
        "feedback.css",
        "dialogs.css",
        "themes.css",
    )
    for css_name in css_names:
        res_sub_css = client.get(f"/static/css/{css_name}")
        assert res_sub_css.status_code == HTTPStatus.OK
        assert "text/css" in res_sub_css.headers.get("content-type", "")

    res_html = client.get("/static/index.html")
    assert res_html.status_code == HTTPStatus.OK
    assert "text/html" in res_html.headers.get("content-type", "")


def test_root_endpoint_status(client: TestClient) -> None:
    """Verify root / endpoint returns operational status message."""
    res = client.get("/")
    assert res.status_code == HTTPStatus.OK
    data = res.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_cross_origin_opener_policy_header(client: TestClient) -> None:
    """Verify Cross-Origin-Opener-Policy is present and set to same-origin."""
    res = client.get("/health")
    assert res.headers.get("Cross-Origin-Opener-Policy") == "same-origin"


def test_cross_origin_resource_policy_header(client: TestClient) -> None:
    """Verify Cross-Origin-Resource-Policy is present and set to same-origin."""
    res = client.get("/health")
    assert res.headers.get("Cross-Origin-Resource-Policy") == "same-origin"


def test_cache_control_no_store_on_api_responses(client: TestClient) -> None:
    """Verify Cache-Control: no-store is attached to all /api responses."""
    for path in ("/api/v1/health", "/api/v1/community/summary"):
        res = client.get(path)
        assert res.headers.get("Cache-Control") == "no-store"


def test_cache_control_omitted_on_static_assets(client: TestClient) -> None:
    """Verify static assets under /static do not carry Cache-Control: no-store."""
    res = client.get("/static/index.html")
    assert res.headers.get("Cache-Control") != "no-store"


def test_rate_limiter_does_not_trust_x_forwarded_for_by_default(client: TestClient) -> None:
    """Verify spoofed X-Forwarded-For is ignored when TRUSTED_PROXY is false."""
    reset_rate_limiter()
    with patch("app.api.middleware.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_per_minute = 2
        mock_settings.return_value.trusted_proxy = False

        res1 = client.get("/health", headers={"X-Forwarded-For": "1.1.1.1"})
        assert res1.status_code == HTTPStatus.OK
        res2 = client.get("/health", headers={"X-Forwarded-For": "2.2.2.2"})
        assert res2.status_code == HTTPStatus.OK

        res3 = client.get("/health", headers={"X-Forwarded-For": "3.3.3.3"})
        assert res3.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_rate_limiter_trusts_x_forwarded_for_when_configured(client: TestClient) -> None:
    """Verify X-Forwarded-For controls rate-limit bucket when TRUSTED_PROXY is true."""
    reset_rate_limiter()
    with patch("app.api.middleware.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_per_minute = 1
        mock_settings.return_value.trusted_proxy = True

        res1 = client.get("/health", headers={"X-Forwarded-For": "203.0.113.195, 10.0.0.1"})
        assert res1.status_code == HTTPStatus.OK

        res2 = client.get("/health", headers={"X-Forwarded-For": "198.51.100.44"})
        assert res2.status_code == HTTPStatus.OK

        res3 = client.get("/health", headers={"X-Forwarded-For": "203.0.113.195"})
        assert res3.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_logs_never_contain_free_text_or_full_coordinates(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify application logs never contain raw user question strings or high-precision GPS."""
    unique_marker = "SENSITIVE_SECRET_MARKER_998877"
    lat = 28.613987654321
    lon = 77.209012345678

    with caplog.at_level(logging.DEBUG):
        res = client.post(
            "/api/v1/ask",
            json={
                "question": f"Is it safe to run? {unique_marker}",
                "facts": {"index_after": 50.0, "latitude": lat, "longitude": lon},
                "language": "en",
            },
        )
        assert res.status_code == HTTPStatus.OK

    log_content = caplog.text
    assert unique_marker not in log_content
    assert str(lat) not in log_content
    assert str(lon) not in log_content
