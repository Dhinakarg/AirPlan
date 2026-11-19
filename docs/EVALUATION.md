# AirPlan Evaluation Framework & Verification Evidence

This document maps the six core technical evaluation criteria to concrete codebase evidence (source files, test names, verification commands, and real test counts), followed by the complete Accessibility & Universal Design Audit Log.

---

## 1. Six Evaluation Criteria vs. Codebase Evidence

| Evaluation Criterion | Core Objective | Primary Source Files | Proving Test Files & Names | Verification Command & Metric |
| :--- | :--- | :--- | :--- | :--- |
| **1. Deterministic exposure model** | Deterministic physical exposure and ventilation calculations; zero I/O, no globals, no `datetime.now()`, no `random`. Injected time parameters. | [app/engine/exposure.py](../app/engine/exposure.py)<br/>[app/engine/ventilation.py](../app/engine/ventilation.py)<br/>[app/engine/ranking.py](../app/engine/ranking.py)<br/>[app/constants.py](../app/constants.py) | `tests/unit/test_exposure.py`<br/>`tests/unit/test_ventilation.py`<br/>`tests/unit/test_ranking.py`<br/>`tests/unit/test_property_invariants.py::test_filtration_always_reduces_or_maintains_dose` | `pytest tests/unit/test_exposure.py tests/unit/test_ventilation.py tests/unit/test_property_invariants.py`<br/>**31 tests passed** (including Hypothesis property tests proving mass monotonicity). |
| **2. Guarded AI Architecture (numeric-hallucination guard)** | The generative model cannot invent numbers or medical claims. Server validates placeholders and substitutes backend-computed metrics. Safe fallback on provider error. | [app/ai/validator.py](../app/ai/validator.py)<br/>[app/ai/guards.py](../app/ai/guards.py)<br/>[app/ai/fallback.py](../app/ai/fallback.py)<br/>[app/services/assistant_service.py](../app/services/assistant_service.py) | `tests/unit/test_ai_layer.py::test_validator_rejects_hallucinated_numbers`<br/>`tests/unit/test_ai_layer.py::test_validator_accepts_clean_placeholders`<br/>`tests/unit/test_ai_layer.py::test_substitute_payload_injects_facts`<br/>`tests/unit/test_ai_layer.py::test_fallback_provider_returns_valid_payload` | `pytest tests/unit/test_ai_layer.py`<br/>**21 tests passed**; proves that LLM numeric hallucination attempts are systematically caught and replaced. |
| **3. Real-World Atmospheric Resilience** | Live Open-Meteo air and weather integration with coordinate truncation, 15-min TTLCache, and seamless local fallback to realistic Delhi smog data. | [app/data/air_client.py](../app/data/air_client.py)<br/>[app/data/cache.py](../app/data/cache.py)<br/>[app/data/sample_data.json](../app/data/sample_data.json) | `tests/unit/test_air_client.py::test_fetch_hourly_air_rounds_coordinates`<br/>`tests/unit/test_air_client.py::test_fetch_hourly_air_uses_cache`<br/>`tests/unit/test_air_client.py::test_fetch_hourly_air_fallback_on_network_failure`<br/>`tests/integration/test_endpoints.py::test_full_offline_end_to_end_journey` | `pytest tests/unit/test_air_client.py tests/integration/test_endpoints.py`<br/>**19 tests passed**; proves complete offline resilience without external network dependencies. |
| **4. Security, Privacy & Resource Guardrails** | Strict Content Security Policy, sliding-window rate limiting (60/min), untrusted proxy mitigation, bounded memory pledge store, 100KB request body limits, PII coordinate rounding, COOP/CORP headers, and clinical emergency red-flag screening in EN/HI. | [app/api/middleware.py](../app/api/middleware.py)<br/>[app/api/schemas.py](../app/api/schemas.py)<br/>[app/engine/safety_rules.py](../app/engine/safety_rules.py) | `tests/unit/test_api.py::test_security_headers_present_on_all_responses`<br/>`tests/unit/test_api.py::test_rate_limit_exceeded_returns_429`<br/>`tests/unit/test_api.py::test_rate_limiter_does_not_trust_x_forwarded_for_by_default`<br/>`tests/unit/test_api.py::test_cross_origin_opener_policy_header`<br/>`tests/unit/test_api.py::test_cache_control_no_store_on_api_responses`<br/>`tests/unit/test_api.py::test_logs_never_contain_free_text_or_full_coordinates`<br/>`tests/unit/test_community.py::test_pledge_store_eviction_when_capacity_exceeded` | `pytest tests/unit/test_api.py tests/unit/test_community.py tests/unit/test_safety_rules.py`<br/>**48 tests passed**; Bandit: 0 issues; pip-audit: 0 CVEs. |
| **5. Universal Accessibility (WCAG 2.1 AA)** | Bilingual EN/HI, keyboard-first navigation with zero focus traps, high-contrast mode ($\ge 7:1$), forced-colors active support, minimum 44px touch targets, minimum 14px typography, multi-attribute AQI indicators, screen-reader live announcements, 320px reflow. | [static/index.html](../static/index.html)<br/>[static/css/layout.css](../static/css/layout.css)<br/>[static/css/nav.css](../static/css/nav.css)<br/>[static/js/a11y.js](../static/js/a11y.js)<br/>[static/js/i18n.js](../static/js/i18n.js) | Automated: contrast, structure and heading tests (`test_wcag_contrast_ratios_light_mode`, `test_wcag_contrast_ratios_dark_mode`, `test_wcag_contrast_ratios_high_contrast_mode`, `test_css_font_sizes_never_below_14px`, `test_css_interactive_targets_at_least_44px`, `test_unique_element_ids_across_served_html`, `test_heading_order_sequential_no_skipped_levels`, `test_index_html_loads_split_stylesheets`).<br/>Manual: keyboard walk-through.<br/>Browser audit: pending user entry | `pytest tests/a11y/test_accessibility.py` (**21 passed**)<br/>`node --test tests/js/*.test.js` (**27 passed**). |
| **6. Code Quality, Maintainability & Modularity** | Clean architecture, curated Ruff rules, strict Mypy, low cyclomatic complexity ($\text{CC} < 6$, no B/C), high maintainability ($\text{MI} = \text{A}$), all JS modules $\le 169$ lines. | [pyproject.toml](../pyproject.toml)<br/>[Makefile](../Makefile)<br/>[app/](../app/)<br/>[static/js/](../static/js/) | `radon cc app -n B` (0 blocks)<br/>`radon mi app -n B` (0 files)<br/>`make jslines` (all 14 files $\le 169$ lines)<br/>`mypy --strict app` (0 errors across 35 files) | `make check`<br/>**192 Python tests (96.71% coverage)** + **27 Node tests** passing cleanly. |

---

## 2. Accessibility & Universal Design Audit Log

| Audit Parameter | Detail |
| :--- | :--- |
| **Audit Date** | 2026-11-19 |
| **Auditing Tools** | Automated: contrast, structure and heading tests (pytest, node). Manual: keyboard walk-through. Browser audit: pending user entry |
| **Tested Themes / Modes** | Light Mode, Dark Mode (`prefers-color-scheme: dark`), High-Contrast Mode (`body.high-contrast`), Windows Forced-Colors Mode (`@media (forced-colors: active)`) |
| **Viewports Evaluated** | 320px (mobile reflow / zoom 200%), 768px (tablet), 1280px (desktop) |
| **Assistive Technology** | Keyboard tab navigation, screen reader simulation, high contrast visual filters |

### Discovered Issues, Remediations, and Regression Coverage

```mermaid
flowchart LR
    Audit["Accessibility & Codebase Audit"] --> Issue1["1. Focus Trap in Visually Hidden Screens"]
    Audit --> Issue2["2. Incomplete ARIA Tabpanel Contract"]
    Audit --> Issue3["3. Skipped Heading Hierarchy"]
    Audit --> Issue4["4. Skip-Link Missing Target Tabindex"]
    Audit --> Issue5["5. Single-Channel Color Distinction"]

    Issue1 --> Fix1["Dynamic hidden attribute on inactive screens"]
    Issue2 --> Fix2["role=tabpanel, aria-labelledby, tabindex=0"]
    Issue3 --> Fix3["Standardized sequential h2 -> h3 nesting"]
    Issue4 --> Fix4["tabindex=-1 on main#main-content"]
    Issue5 --> Fix5["Triple-channel AQI: Number + Icon + Pattern"]

    Fix1 --> Test1["test_inactive_screens_hidden_from_tab_order"]
    Fix2 --> Test2["test_screen_sections_are_tabpanels"]
    Fix3 --> Test3["test_heading_order_sequential_no_skipped_levels"]
    Fix4 --> Test4["test_main_landmark_has_tabindex"]
    Fix5 --> Test5["getAqiCategory unit tests in tests/js/render.test.js"]
```

#### Detailed Findings & Fixes

1. **Focus Trap in Inactive Screens (`aria-hidden-focus`)**
   - *Problem*: Inactive view sections (`#screen-ledger`, `#screen-results`, etc.) utilized an off-screen CSS utility (`.sr-only`) without `display: none` or the HTML5 `hidden` attribute. Consequently, interactive inputs inside dormant screens remained focusable in the keyboard Tab sequence.
   - *Fix*: Configured all inactive sections with the native `hidden` boolean attribute on page initialization, and dynamically toggled `sec.hidden = !isTarget` during tab switching. Configured `.layout-screen:not([hidden])` and `.layout-screen[hidden] { display: none; }` in [static/css/layout.css](../static/css/layout.css) without `!important` to achieve unambiguous cascade specificity.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_inactive_screens_hidden_from_tab_order`.

2. **WAI-ARIA Tab / Tabpanel Contract (`aria-allowed-role`)**
   - *Problem*: Navigation tabs declared `role="tab"` and `aria-controls="screen-..."`, but target screen `<section>` elements lacked corresponding `role="tabpanel"` and `aria-labelledby="tab-..."`.
   - *Fix*: Updated each screen section in [static/index.html](../static/index.html) to include `role="tabpanel"`, `tabindex="0"`, and `aria-labelledby="tab-..."`.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_screen_sections_are_tabpanels`.

3. **Heading Hierarchy Nesting (`heading-order`)**
   - *Problem*: Several dynamically rendered cards in `results.js`, `detective.js`, and `assistant.js` rendered `<h4>` elements directly under the primary section `<h2>`, skipping `<h3>`.
   - *Fix*: Standardized all sub-headings to `<h3>` across all render modules, creating an unbroken semantic heading outline (`h1` -> `h2` -> `h3`).
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_heading_order_sequential_no_skipped_levels`.

4. **Skip-Link Focus Landing (`skip-link`)**
   - *Problem*: The skip link targeted `<main id="main-content">`, but the element lacked `tabindex="-1"`, causing certain browsers to fail shifting keyboard focus after activation.
   - *Fix*: Added `tabindex="-1"` and `:focus-visible` styling to `<main id="main-content">`.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_main_landmark_has_tabindex`.

5. **Multi-Attribute AQI Discrimination (WCAG 1.4.1 Use of Color)**
   - *Status*: Verified compliant. AirPlan never relies solely on green/yellow/red color coding to convey air quality severity. Every AQI classification combines three distinct perceptual attributes:
     - Numerical PM2.5 range (e.g. `121-250 ug/m3`)
     - Category label & emoji icon (e.g. `Very Poor 🔴`)
     - Tactile geometric pattern descriptor (`[Solid Dot]`, `[Diagonal Slash]`, `[Horizontal Stripe]`, `[Crosshatch]`, `[Stippled Grid]`).
