"""Visual accessibility test suite verifying WCAG contrast ratios, typography, targets."""

import re
from http import HTTPStatus
from pathlib import Path

from starlette.testclient import TestClient

from tests.a11y.dom_parser import get_served_html


def test_index_html_loads_split_stylesheets(client: TestClient) -> None:
    """Verify index.html loads modular split stylesheets in strict cascade order."""
    html = get_served_html(client)
    expected_stylesheets = [
        "/static/css/tokens.css",
        "/static/css/base.css",
        "/static/css/layout.css",
        "/static/css/nav.css",
        "/static/css/buttons.css",
        "/static/css/cards.css",
        "/static/css/forms.css",
        "/static/css/results.css",
        "/static/css/feedback.css",
        "/static/css/dialogs.css",
        "/static/css/themes.css",
    ]
    for css_url in expected_stylesheets:
        assert f'href="{css_url}"' in html, f"Missing stylesheet link: {css_url}"
        res = client.get(css_url)
        assert res.status_code == HTTPStatus.OK, f"Stylesheet not served (200): {css_url}"

    positions = [html.find(f'href="{css_url}"') for css_url in expected_stylesheets]
    assert positions == sorted(positions), (
        "Stylesheets are not loaded in expected cascade order in index.html"
    )


def test_no_innerhtml_in_static_js() -> None:
    """Ensure zero occurrences of dangerous innerHTML usage across static/js."""
    js_dir = Path(__file__).resolve().parent.parent.parent / "static" / "js"
    js_files = list(js_dir.rglob("*.js"))
    assert len(js_files) > 0

    violations: list[str] = []
    for js_file in js_files:
        content = js_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            if "innerHTML" in line:
                violations.append(f"{js_file.name}:{idx}: {line.strip()}")

    assert not violations, "Forbidden innerHTML detected:\n" + "\n".join(violations)


def test_css_and_js_file_line_limits() -> None:
    """Enforce architectural limits: every CSS file <= 200 lines, every JS file <= 150 lines."""
    static_dir = Path(__file__).resolve().parent.parent.parent / "static"
    css_files = list((static_dir / "css").glob("*.css"))
    js_files = list((static_dir / "js").rglob("*.js"))

    assert len(css_files) >= 10, f"Expected split CSS files, found {len(css_files)}"
    assert len(js_files) >= 10, f"Expected split JS files, found {len(js_files)}"

    css_violations: list[tuple[str, int]] = []
    for cf in css_files:
        line_count = len(cf.read_text(encoding="utf-8").splitlines())
        if line_count > 200:
            css_violations.append((cf.name, line_count))

    js_violations: list[tuple[str, int]] = []
    for jf in js_files:
        line_count = len(jf.read_text(encoding="utf-8").splitlines())
        if line_count > 150:
            js_violations.append((jf.name, line_count))

    assert not css_violations, f"CSS files exceeding 200 lines: {css_violations}"
    assert not js_violations, f"JS files exceeding 150 lines: {js_violations}"


def _srgb_to_linear(val: float) -> float:
    """Convert normalized sRGB channel to linear light value."""
    return val / 12.92 if val <= 0.04045 else ((val + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_code: str) -> float:
    """Compute relative luminance for sRGB hex string per WCAG 2.1 formula."""
    hex_clean = hex_code.lstrip("#")
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute contrast ratio between two hex colors per WCAG 2.1 formula."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def test_wcag_contrast_ratios_light_mode() -> None:
    """Verify all light mode text pairs are >= 4.5:1 and UI borders >= 3:1."""
    bg_surface = "#ffffff"
    text_tokens = [
        ("#0f172a", "text-primary"),
        ("#334155", "text-secondary"),
        ("#475569", "text-muted"),
        ("#0f766e", "color-accent"),
        ("#166534", "color-success"),
        ("#92400e", "color-warning"),
        ("#991b1b", "color-danger"),
        ("#075985", "color-info"),
    ]
    for hex_val, name in text_tokens:
        ratio = _contrast_ratio(hex_val, bg_surface)
        assert ratio >= 4.5, f"Light mode token {name} ({hex_val}) contrast {ratio:.2f} < 4.5:1"

    ui_tokens = [
        ("#64748b", "border-strong"),
        ("#0284c7", "color-focus"),
    ]
    for hex_val, name in ui_tokens:
        ratio = _contrast_ratio(hex_val, bg_surface)
        assert ratio >= 3.0, f"Light mode UI token {name} ({hex_val}) contrast {ratio:.2f} < 3:1"


def test_wcag_contrast_ratios_dark_mode() -> None:
    """Verify all dark mode text pairs are >= 4.5:1 and UI borders >= 3:1."""
    bg_surface = "#111827"
    text_tokens = [
        ("#f8fafc", "text-primary"),
        ("#e2e8f0", "text-secondary"),
        ("#cbd5e1", "text-muted"),
        ("#2dd4bf", "color-accent"),
        ("#4ade80", "color-success"),
        ("#fbbf24", "color-warning"),
        ("#f87171", "color-danger"),
        ("#38bdf8", "color-info"),
    ]
    for hex_val, name in text_tokens:
        ratio = _contrast_ratio(hex_val, bg_surface)
        assert ratio >= 4.5, f"Dark mode token {name} ({hex_val}) contrast {ratio:.2f} < 4.5:1"

    ui_tokens = [
        ("#94a3b8", "border-strong"),
        ("#38bdf8", "color-focus"),
    ]
    for hex_val, name in ui_tokens:
        ratio = _contrast_ratio(hex_val, bg_surface)
        assert ratio >= 3.0, f"Dark mode UI token {name} ({hex_val}) contrast {ratio:.2f} < 3:1"


def test_wcag_contrast_ratios_high_contrast_mode() -> None:
    """Verify high contrast mode achieves enhanced contrast >= 7:1 for text and >= 3:1 borders."""
    bg = "#000000"
    text_tokens = [
        ("#ffffff", "text-primary / text-muted"),
        ("#ffff00", "text-secondary"),
        ("#00ffff", "color-accent"),
        ("#55ff55", "color-success"),
        ("#ffff55", "color-warning"),
        ("#ff7070", "color-danger"),
        ("#55ffff", "color-info"),
    ]
    for hex_val, name in text_tokens:
        ratio = _contrast_ratio(hex_val, bg)
        assert ratio >= 7.0, (
            f"High contrast text token {name} ({hex_val}) contrast {ratio:.2f} < 7:1"
        )

    ui_tokens = [
        ("#ffffff", "border-strong / border-subtle / border-card"),
        ("#ffff00", "color-focus"),
        ("#00ffff", "color-accent-border"),
    ]
    for hex_val, name in ui_tokens:
        ratio = _contrast_ratio(hex_val, bg)
        assert ratio >= 3.0, f"High contrast UI token {name} ({hex_val}) contrast {ratio:.2f} < 3:1"


def test_css_font_sizes_never_below_14px() -> None:
    """CSS parser verifies no typography rule falls below 14px (0.875rem)."""
    css_dir = Path(__file__).resolve().parent.parent.parent / "static" / "css"
    for css_file in css_dir.glob("*.css"):
        content = css_file.read_text(encoding="utf-8")
        px_matches = re.findall(r"font-size:\s*(\d+)px", content)
        for px in px_matches:
            assert int(px) >= 14, f"Font size {px}px in {css_file.name} is below 14px limit"

        rem_matches = re.findall(r"font-size:\s*([0-9.]+)rem", content)
        for rem in rem_matches:
            assert float(rem) >= 0.875, (
                f"Font size {rem}rem in {css_file.name} is below 0.875rem (14px)"
            )


def test_css_interactive_targets_at_least_44px() -> None:
    """CSS parser verifies interactive components declare at least 44px touch targets."""
    tokens_css = Path(__file__).resolve().parent.parent.parent / "static" / "css" / "tokens.css"
    content = tokens_css.read_text(encoding="utf-8")
    match = re.search(r"--target-min:\s*(\d+)px", content)
    assert match is not None
    assert int(match.group(1)) >= 44
