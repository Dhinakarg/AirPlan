"""HTML DOM parser and helper utilities for accessibility audits."""

from html.parser import HTMLParser
from http import HTTPStatus

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

    def _record_element_id_and_live(self, _tag: str, attrs: dict[str, str | None]) -> None:
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
        """Track closing tags."""
        if tag == "label":
            self.inside_label = False


def get_served_html(client: TestClient) -> str:
    """Fetch served index.html content via TestClient."""
    res = client.get("/static/index.html")
    assert res.status_code == HTTPStatus.OK
    return str(res.text)
