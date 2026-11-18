# AirPlan Implementation Plan

AirPlan is a GenAI-assisted household clean-air planner for families and communities facing severe winter smog.
It builds hour-by-hour exposure plans per family member, identifies likely indoor pollution sources, ranks low-cost interventions, and shows every choice's impact with stated assumptions and confidence (provenance).

## 1. Directory Structure & Architecture
Strict one-way import flow: `app/api` -> `app/services` -> `app/engine`, `app/data`, `app/ai`.
- `app/`
  - `__init__.py`
  - `constants.py`: Named domain constants, physical factors, WHO/NAAQS thresholds, units, limits.
  - `config.py`: Environment-driven validated settings via Pydantic.
  - `errors.py`: Domain exception hierarchy.
  - `engine/` (Pure: no I/O, no network, no globals, no datetime.now, no random)
    - `__init__.py`
    - `models.py`: Pydantic domain models with Provenance & Confidence.
    - `indoor_model.py`: Single-zone dynamic mass-balance PM2.5 box model.
    - `source_detector.py`: Indoor emission source finding and peak characterization.
    - `interventions.py`: Low-cost intervention modeling, impact estimation, cost-effectiveness ranking.
    - `exposure_planner.py`: Hour-by-hour member exposure calculation, routine analysis, WHO comparison.
  - `data/` (No imports from engine/ai)
    - `__init__.py`
    - `forecast_data.py`: Diurnal winter smog profile generators and offline sample datasets.
  - `ai/` (Imports engine.models only)
    - `__init__.py`
    - `provider.py`: Deterministic fallback template AI + optional Google GenAI provider with prompt injection defense.
  - `services/`
    - `__init__.py`
    - `plan_service.py`: Service orchestrating data, engine, AI; timestamp injection; caching.
  - `api/` (Parse -> call service -> return only)
    - `__init__.py`
    - `middleware.py`: Security headers, correlation ID, rate limiter, safe location logging.
    - `router.py`: REST endpoints (/api/health, /api/forecast, /api/plan, /api/interventions, /api/explain).
  - `main.py`: FastAPI app initialization and static file mounting.
- `static/`
  - `index.html`: WCAG 2.1 AA accessible single-page interface with English & Hindi support.
  - `css/style.css`: High contrast, responsive, prefers-color-scheme, prefers-reduced-motion.
  - `js/`
    - `main.js`: Application bootstrapper.
    - `state.js`: Reactive state store.
    - `api.js`: Client API module.
    - `i18n.js`: English and Hindi localization dictionary and formatter.
    - `a11y.js`: Accessibility announcer and focus manager.
    - `render/common.js`: Safe DOM creation utilities (strictly textContent/createElement).
    - `render/sources.js`: Source findings view.
    - `render/interventions.js`: Ranked interventions view.
    - `render/timeline.js`: Accessible hourly chart and tabular exposure ledger.
    - `render/members.js`: Family member cards and personal guidance.
    - `render/summary.js`: AI narrative, plain language mode, provenance badges.
- `tests/`
  - `conftest.py`: Fixtures for household profiles, members, forecast data.
  - `test_indoor_model.py`: Mass balance invariants, edge cases, hypothesis property tests.
  - `test_source_detector.py`: Source detection, emission rates, exhaust impacts.
  - `test_interventions.py`: DIY purifier vs sealing vs masking, cost ranking.
  - `test_exposure_planner.py`: Member exposure timelines, vulnerability weighting.
  - `test_plan_service.py`: Orchestration, deterministic execution.
  - `test_api.py`: FastAPI endpoints, validation, security headers, correlation ID, error handling.
  - `test_ai.py`: Prompt sanitizer and template engine fallback.
  - `test_architecture.py`: AST/import-linter test enforcing strict one-way import rules.
  - `frontend/`:
    - `state.test.js`: State store tests.
    - `i18n.test.js`: Localization dictionary tests.
    - `a11y.test.js`: Accessible utilities tests.
- `Makefile`: Quality check runner (`make check`).
- `pyproject.toml`: Configuration for ruff, mypy, pytest, coverage.

## 2. Execution Steps
1. Create `pyproject.toml` and `Makefile`.
2. Implement `app/constants.py`, `app/errors.py`, and `app/config.py`.
3. Implement `app/engine/models.py`.
4. Implement pure engine modules: `indoor_model.py`, `source_detector.py`, `interventions.py`, `exposure_planner.py`.
5. Implement `app/data/forecast_data.py`.
6. Implement `app/ai/provider.py`.
7. Implement `app/services/plan_service.py`.
8. Implement `app/api/middleware.py`, `app/api/router.py`, `app/main.py`.
9. Implement accessible frontend: `index.html`, `style.css`, ES modules.
10. Implement comprehensive unit, property, and integration tests.
11. Run `make check` (ruff, mypy, bandit, pytest coverage >= 90%, node tests) and verify zero errors.
12. Commit with conventional commits.

