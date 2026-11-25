"""DOM structure and semantic accessibility test suite (landmarks, headings, labels)."""

from starlette.testclient import TestClient

from tests.a11y.dom_parser import DocumentParser, get_served_html


def test_html_lang_attribute(client: TestClient) -> None:
    """Ensure html tag has lang='en' attribute."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert parser.html_attrs.get("lang") == "en"


def test_single_h1_heading(client: TestClient) -> None:
    """Ensure exactly one h1 element exists."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert parser.h1_count == 1


def test_required_landmarks_present(client: TestClient) -> None:
    """Ensure required ARIA landmarks are present."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert "main" in parser.landmarks
    assert "navigation" in parser.landmarks or "nav" in parser.landmarks


def test_skip_link_first_element(client: TestClient) -> None:
    """Ensure skip link exists and points to #main-content."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert parser.first_link_href == "#main-content"
    assert parser.first_link_class is not None
    assert "skip-link" in parser.first_link_class


def test_main_landmark_has_tabindex(client: TestClient) -> None:
    """Ensure <main id='main-content'> element declares tabindex='-1'."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert parser.main_attrs.get("id") == "main-content"
    assert parser.main_attrs.get("tabindex") == "-1"


def test_screen_sections_are_tabpanels(client: TestClient) -> None:
    """Ensure screen sections declare role='tabpanel', tabindex='0', and aria-labelledby."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert len(parser.screen_sections) >= 3
    for sec in parser.screen_sections:
        assert sec.get("role") == "tabpanel"
        assert sec.get("tabindex") == "0"
        assert sec.get("aria-labelledby") is not None


def test_inactive_screens_hidden_from_tab_order(client: TestClient) -> None:
    """Ensure inactive screen sections carry hidden attribute."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    screen_results = next(s for s in parser.screen_sections if s.get("id") == "screen-results")
    assert "hidden" in screen_results


def test_all_inputs_have_associated_labels(client: TestClient) -> None:
    """Ensure all inputs have an associated label."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert len(parser.inputs_and_selects) > 0
    for ctrl in parser.inputs_and_selects:
        ctrl_id = ctrl.get("id")
        has_for_label = ctrl_id in parser.label_for_targets if ctrl_id else False
        is_nested = ctrl.get("nested_in_label") == "true"
        has_aria_label = bool(ctrl.get("aria-label") or ctrl.get("aria-labelledby"))
        assert has_for_label or is_nested or has_aria_label, f"Unlabelled form control: {ctrl}"


def test_no_inline_scripts_or_handlers(client: TestClient) -> None:
    """Ensure zero inline scripts or event handlers (CSP compliance)."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert len(parser.inline_scripts) == 0, f"Found inline scripts: {parser.inline_scripts}"
    assert len(parser.inline_event_handlers) == 0, (
        f"Found inline event handlers: {parser.inline_event_handlers}"
    )


def test_table_has_caption_and_th_scopes(client: TestClient) -> None:
    """Ensure data tables provide caption and scoped header cells."""
    html = get_served_html(client)
    parser = DocumentParser()
    parser.feed(html)
    if parser.tables_count > 0:
        assert parser.table_has_caption
        assert len(parser.table_th_scopes) > 0
        for scope in parser.table_th_scopes:
            assert scope in ("col", "row")


def test_step_layout_exists_in_served_html(client: TestClient) -> None:
    """Verify that .step-layout container exists in served index.html."""
    html = get_served_html(client)
    assert "step-layout" in html


def test_unique_element_ids_across_served_html(client: TestClient) -> None:
    """Verify all element IDs in served HTML document are strictly unique."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    total_ids = len(parser.all_ids)
    unique_ids = len(set(parser.all_ids))
    assert total_ids > 0
    assert total_ids == unique_ids, (
        f"Found duplicate IDs: {[x for x in parser.all_ids if parser.all_ids.count(x) > 1]}"
    )


def test_aria_live_regions_present_on_served_html(client: TestClient) -> None:
    """Verify essential live announcing regions are configured with polite or alert modes."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    live_ids = [r.get("id") for r in parser.aria_live_regions if r.get("id")]
    assert "status-announcer" in live_ids
    assert "error-alert" in live_ids
    assert "toast-container" in live_ids


def test_heading_order_sequential_no_skipped_levels(client: TestClient) -> None:
    """Verify heading levels follow strict sequential descending hierarchy without skips."""
    parser = DocumentParser()
    parser.feed(get_served_html(client))
    assert len(parser.heading_levels) > 0
    current_level = parser.heading_levels[0]
    assert current_level == 1  # Root page heading must be h1

    for level in parser.heading_levels[1:]:
        assert level <= current_level + 1, (
            f"Skipped heading level: jumped from h{current_level} to h{level}"
        )
        current_level = level
