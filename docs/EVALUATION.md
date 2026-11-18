# Evaluation Methodology & Metrics

This document outlines the evaluation framework for AirLedger's clean-air recommendations, mathematical model accuracy, and community intervention impact.

## 1. Physical Accuracy Metrics
- **Mean Absolute Error (MAE)** against calibrated reference indoor monitor data.
- **Root Mean Square Error (RMSE)** for single-zone mass balance transient response during cooking and filtration events.
- **Physical Monotonicity Invariants**: Verification via property-based testing (Hypothesis) that filtration always reduces or maintains particulate concentration.

## 2. Health & Vulnerability Metrics
- **Time-Weighted Daily Average Inhaled Dose**: Exposure calculation across heterogeneous activity schedules.
- **WHO & NAAQS Threshold Exceedance Hours**: Tracking hours above 15 $\mu\text{g/m}^3$ (WHO) and 60 $\mu\text{g/m}^3$ (Indian standard).
- **Vulnerability-Adjusted Risk Multiplier**: Individualized physiological sensitivity weightings for infants, elderly, and respiratory patients.

## 3. Intervention Cost-Effectiveness
- **$\Delta\text{PM}_{2.5} / \text{Cost}$ Ratio**: Micrograms per cubic meter reduction per 100 INR spent on low-cost mitigations (e.g. Corsi-Rosenthal boxes, weatherstripping, N95 masks).

## 4. Accessibility & Inclusive Design Audit Log

| Field | Detail |
| :--- | :--- |
| **Audit Date** | 2026-11-18 |
| **Auditing Tools** | Browser Subagent, axe-core v4.10.2 (WCAG 2.1 AA / Section 508), DOM Inspection |
| **Evaluated Modes** | Light, Dark (`prefers-color-scheme: dark`), and High-Contrast (`body.high-contrast`) |
| **Viewports Tested** | 320px (reflow / zoom 200%), 768px (tablet), 1280px (desktop) |

### Findings & Remediation

1. **Focus Trap in Visually Hidden Screens (`aria-hidden-focus`)**
   - *Issue*: Inactive screen sections (`#screen-ledger`, `#screen-results`, etc.) used `.sr-only` class without `display: none` or the `hidden` attribute. Form controls inside inactive screens remained in the keyboard Tab order.
   - *Fix*: Applied native `hidden` attribute to inactive sections upon initialization and dynamically toggled `sec.hidden = !isTarget` in `switchScreen()`. Added `.layout-screen[hidden] { display: none !important; }` in CSS.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_inactive_screens_hidden_from_tab_order`.

2. **WAI-ARIA Tabpanel Relationship (`aria-allowed-role`)**
   - *Issue*: Navigation tabs declared `role="tab"` with `aria-controls="screen-..."`, but target `<section>` elements lacked corresponding `role="tabpanel"` and `tabindex="0"`.
   - *Fix*: Updated each screen `<section>` in `static/index.html` with `role="tabpanel"`, `tabindex="0"`, and `aria-labelledby="tab-..."`.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_screen_sections_are_tabpanels`.

3. **Heading Hierarchy Non-Sequential Nesting (`heading-order`)**
   - *Issue*: Sub-sections in results, detective, and assistant components rendered `<h4>` elements directly beneath the container `<h2>`, skipping `<h3>`.
   - *Fix*: Standardized subheadings across all render modules (`results.js`, `detective.js`, `ledger.js`, `neighbourhood.js`, `assistant.js`) to `<h3>`.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_table_has_caption_and_th_scopes`.

4. **Skip Link Focus Target (`skip-link`)**
   - *Issue*: `#main-content` lacked `tabindex="-1"`, causing inconsistent programmatic focus shifts on older browser engines following skip link activation.
   - *Fix*: Added `tabindex="-1"` to `<main id="main-content">` and configured `:focus-visible` ring.
   - *Regression Test*: `tests/a11y/test_accessibility.py::test_main_landmark_has_tabindex`.

5. **Multi-Attribute AQI Discrimination (WCAG 1.4.1)**
   - *Status*: Verified compliant. Particulate categories are distinguished via three redundant channels: numeric range text, graphical emoji icon, and pattern descriptor (`[Solid Dot]`, `[Diagonal Slash]`, `[Horizontal Stripe]`, `[Crosshatch]`, `[Stippled Grid]`).
