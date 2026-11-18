"""Accessibility compliance test suite verifying WCAG AA, landmarks, labels, and scripts."""

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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Process element start tags and record attributes for accessibility audits.

        Args:
            tag: HTML tag name.
            attrs: List of attribute name-value tuples.
        """
        attr_dict = dict(attrs)
        self.current_tag = tag

        if tag == "html":
            self.html_attrs = attr_dict
        elif tag == "h1":
            self.h1_count += 1
        elif tag in ("header", "nav", "main", "footer"):
            self.landmarks.add(tag)

        role = attr_dict.get("role")
        if role in ("banner", "navigation", "main", "contentinfo"):
            self.landmarks.add(role)

        self._check_first_link(tag, attr_dict)
        self._check_form_controls(tag, attr_dict)
        self._check_scripts_and_events(tag, attr_dict)
        self._check_table_elements(tag, attr_dict)

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
    # Also test table rendered in static HTML or generated DOM template
    # Read results.js template / html parser
    html = _get_served_html(client)
    # If table is present in index.html, verify it; otherwise test table renderer directly
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
