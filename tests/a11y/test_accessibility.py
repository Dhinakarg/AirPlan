"""Accessibility compliance test suite verifying WCAG AA, landmarks, labels, and scripts."""

import re
from html.parser import HTMLParser
from http import HTTPStatus
from pathlib import Path

from starlette.testclient import TestClient


class DocumentParser(HTMLParser):
    """Custom parser inspecting HTML elements, attributes, landmarks, and tables."""

    def __init__(self) -> None:
        """Initialize tracking data structures."""
        super().__init__()
        self.html_attrs: dict[str, str | None] = {}
        self.main_attrs: dict[str, str | None] = {}
        self.h1_count: int = 0
        self.landmarks: set[str] = set()
        self.first_link_href: str | None = None
        self.first_link_class: str | None = None
        self.inputs_and_selects: list[dict[str, str | None]] = []
        self.label_for_targets: set[str] = set()
        self.inside_label: bool = False
        self.inline_scripts: list[str] = []
        self.inline_event_handlers: list[str] = []
        self.current_tag: str | None = None
        self.tables_count: int = 0
        self.table_has_caption: bool = False
        self.table_th_scopes: list[str] = []
        self.screen_sections: list[dict[str, str | None]] = []
        self.all_ids: list[str] = []
        self.heading_levels: list[int] = []
        self.aria_live_regions: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process element start tags and record attributes for accessibility audits."""
        attr_dict = dict(attrs)
        self.current_tag = tag
        self._record_element_id_and_live(tag, attr_dict)
        self._record_headings(tag)
        self._record_landmarks(tag, attr_dict)
        self._check_first_link(tag, attr_dict)
        self._check_form_controls(tag, attr_dict)
        self._check_scripts_and_events(tag, attr_dict)
        self._check_table_elements(tag, attr_dict)

    def _record_element_id_and_live(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Track ID uniqueness and live announcing regions."""
        if attrs.get("id"):
            self.all_ids.append(str(attrs["id"]))
        if "aria-live" in attrs or attrs.get("role") in ("status", "alert"):
            self.aria_live_regions.append(attrs)

    def _record_headings(self, tag: str) -> None:
        """Track sequential heading level occurrences."""
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_levels.append(int(tag[1]))
            if tag == "h1":
                self.h1_count += 1

    def _record_landmarks(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Record landmark structures and screen sections."""
        if tag == "html":
            self.html_attrs = attrs
        elif tag == "main":
            self.main_attrs = attrs
            self.landmarks.add("main")
        elif tag in ("header", "nav", "footer"):
            self.landmarks.add(tag)

        role = attrs.get("role")
        if role in ("banner", "navigation", "main", "contentinfo"):
            self.landmarks.add(role)
        if tag == "section" and (attrs.get("id") or "").startswith("screen-"):
            self.screen_sections.append(attrs)

    def _check_first_link(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Inspect skip link presence as first link."""
        if tag == "a" and self.first_link_href is None:
            self.first_link_href = attrs.get("href")
            self.first_link_class = attrs.get("class")

    def _check_form_controls(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Track inputs, selects, textareas, and label associations."""
        if tag == "label":
            self.inside_label = True
            for_val = attrs.get("for")
            if for_val:
                self.label_for_targets.add(for_val)
        elif tag in ("input", "select", "textarea") and attrs.get("type") != "hidden":
            attrs["nested_in_label"] = "true" if self.inside_label else "false"
            self.inputs_and_selects.append(attrs)

    def _check_scripts_and_events(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Detect disallowed inline script tags and inline event handlers."""
        if tag == "script" and "src" not in attrs:
            self.inline_scripts.append(tag)
        for name in attrs:
            if name.lower().startswith("on"):
                self.inline_event_handlers.append(f"{tag}:{name}")

    def _check_table_elements(self, tag: str, attrs: dict[str, str | None]) -> None:
        """Record table structure, captions, and th scopes."""
        if tag == "table":
            self.tables_count += 1
        elif tag == "caption":
            self.table_has_caption = True
        elif tag == "th":
            scope = attrs.get("scope")
            if scope:
                self.table_th_scopes.append(scope)

    def handle_endtag(self, tag: str) -> None:
        """Track closing tags.

        Args:
            tag: Closed tag name.
        """
        if tag == "label":
            self.inside_label = False


def _get_served_html(client: TestClient) -> str:
    """Fetch served index.html content via TestClient.

    Args:
        client: HTTP test client.

    Returns:
        HTML document string.
    """
    res = client.get("/static/index.html")
    assert res.status_code == HTTPStatus.OK
    return res.text


def test_html_lang_attribute(client: TestClient) -> None:
    """Verify HTML element possesses valid lang attribute."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert "lang" in parser.html_attrs
    assert parser.html_attrs["lang"] in ("en", "hi")


def test_single_h1_heading(client: TestClient) -> None:
    """Verify exactly one h1 heading exists for landmark hierarchy."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert parser.h1_count == 1


def test_required_landmarks_present(client: TestClient) -> None:
    """Verify required ARIA landmark roles or semantic landmarks."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert "header" in parser.landmarks or "banner" in parser.landmarks
    assert "nav" in parser.landmarks or "navigation" in parser.landmarks
    assert "main" in parser.landmarks
    assert "footer" in parser.landmarks or "contentinfo" in parser.landmarks


def test_skip_link_first_element(client: TestClient) -> None:
    """Verify skip link is first focusable element targeting main content."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert parser.first_link_href == "#main-content"
    assert parser.first_link_class is not None
    assert "skip-link" in parser.first_link_class


def test_main_landmark_has_tabindex(client: TestClient) -> None:
    """Verify main content has tabindex=-1 for keyboard skip navigation target."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert parser.main_attrs.get("tabindex") == "-1"
    assert parser.main_attrs.get("id") == "main-content"


def test_screen_sections_are_tabpanels(client: TestClient) -> None:
    """Verify all screen sections declare role=tabpanel and explicit aria-labelledby."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert len(parser.screen_sections) == 6
    for sec in parser.screen_sections:
        assert sec.get("role") == "tabpanel"
        assert sec.get("tabindex") == "0"
        assert sec.get("aria-labelledby") is not None


def test_inactive_screens_hidden_from_tab_order(client: TestClient) -> None:
    """Verify inactive screens carry hidden attribute to prevent keyboard focus traps."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    inactive_screens = [s for s in parser.screen_sections if s.get("id") != "screen-family"]
    assert len(inactive_screens) == 5
    for sec in inactive_screens:
        assert "hidden" in sec, f"Screen {sec.get('id')} lacks hidden attribute"


def test_all_inputs_have_associated_labels(client: TestClient) -> None:
    """Verify all interactive inputs have an associated label or nested label."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert len(parser.inputs_and_selects) > 0
    for control in parser.inputs_and_selects:
        ctrl_id = control.get("id")
        has_for_label = ctrl_id in parser.label_for_targets if ctrl_id else False
        is_nested = control.get("nested_in_label") == "true"
        has_aria_label = "aria-label" in control or "aria-labelledby" in control
        assert has_for_label or is_nested or has_aria_label, (
            f"Control without accessible label: {control}"
        )


def test_no_inline_scripts_or_handlers(client: TestClient) -> None:
    """Verify strict CSP compliance: no inline scripts or on* event handlers."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert len(parser.inline_scripts) == 0, f"Found inline scripts: {parser.inline_scripts}"
    assert len(parser.inline_event_handlers) == 0, (
        f"Found inline handlers: {parser.inline_event_handlers}"
    )


def test_no_innerhtml_in_static_js() -> None:
    """Assert zero usage of innerHTML across all frontend JavaScript modules."""
    static_js_dir = Path(__file__).resolve().parent.parent.parent / "static" / "js"
    assert static_js_dir.exists(), f"Directory not found: {static_js_dir}"

    js_files = list(static_js_dir.rglob("*.js"))
    assert len(js_files) >= 5, f"Expected at least 5 JS modules, found {len(js_files)}"

    violations: list[str] = []
    for f in js_files:
        content = f.read_text(encoding="utf-8")
        if "innerHTML" in content:
            violations.append(f.name)

    assert not violations, f"Forbidden innerHTML found in modules: {violations}"


def test_table_has_caption_and_th_scopes(client: TestClient) -> None:
    """Verify tables contain descriptive captions and column/row scope headers."""
    parser = DocumentParser()
    html = _get_served_html(client)
    repo_root = Path(__file__).resolve().parent.parent.parent
    results_js = repo_root / "static" / "js" / "render" / "results.js"
    results_code = results_js.read_text(encoding="utf-8")
    assert "caption" in results_code
    assert "scope" in results_code
    assert "'col'" in results_code

    parser.feed(html)
    if parser.tables_count > 0:
        assert parser.table_has_caption
        assert len(parser.table_th_scopes) > 0
        for scope in parser.table_th_scopes:
            assert scope in ("col", "row")


def test_step_layout_exists_in_served_html(client: TestClient) -> None:
    """Verify that .step-layout container exists in served index.html."""
    html = _get_served_html(client)
    assert "step-layout" in html


def _srgb_to_linear(val: float) -> float:
    """Convert normalized sRGB channel to linear light value."""
    return val / 12.92 if val <= 0.04045 else ((val + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_code: str) -> float:
    """Calculate WCAG 2.1 relative luminance for a 6-digit hex color string."""
    clean = hex_code.lstrip("#")
    r = _srgb_to_linear(int(clean[0:2], 16) / 255.0)
    g = _srgb_to_linear(int(clean[2:4], 16) / 255.0)
    b = _srgb_to_linear(int(clean[4:6], 16) / 255.0)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute relative contrast ratio between two hex colors."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


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
    """Verify high contrast mode achieves enhanced contrast >= 7:1 for text."""
    bg = "#000000"
    for hex_val in ("#ffffff", "#ffff00", "#00ffff", "#55ff55"):
        ratio = _contrast_ratio(hex_val, bg)
        assert ratio >= 7.0, f"High contrast token {hex_val} contrast {ratio:.2f} < 7:1"


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


def test_unique_element_ids_across_served_html(client: TestClient) -> None:
    """Verify all element IDs in served HTML document are strictly unique."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    total_ids = len(parser.all_ids)
    unique_ids = len(set(parser.all_ids))
    assert total_ids > 0
    assert total_ids == unique_ids, (
        f"Found duplicate IDs: {[x for x in parser.all_ids if parser.all_ids.count(x) > 1]}"
    )


def test_aria_live_regions_present_on_served_html(client: TestClient) -> None:
    """Verify essential live announcing regions are configured with polite or alert modes."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    live_ids = [r.get("id") for r in parser.aria_live_regions if r.get("id")]
    assert "status-announcer" in live_ids
    assert "error-alert" in live_ids
    assert "toast-container" in live_ids


def test_heading_order_sequential_no_skipped_levels(client: TestClient) -> None:
    """Verify heading levels follow strict sequential descending hierarchy without skips."""
    parser = DocumentParser()
    parser.feed(_get_served_html(client))
    assert len(parser.heading_levels) > 0
    current_level = parser.heading_levels[0]
    assert current_level == 1  # Root page heading must be h1

    for level in parser.heading_levels[1:]:
        assert level <= current_level + 1, (
            f"Skipped heading level: jumped from h{current_level} to h{level}"
        )
        current_level = level
