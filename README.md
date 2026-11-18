# AirLedger

> **GenAI-assisted household clean-air planner for families and communities facing severe winter smog.**

AirLedger models hour-by-hour particulate exposure ($PM_{2.5}$), detects likely indoor pollution sources (chulha/biomass stoves, incense, mosquito coils, smoking), ranks low-cost interventions (DIY Corsi-Rosenthal box purifiers, weatherstripping, N95 respirators, routine shifting), and demonstrates every recommendation's impact with stated assumptions and confidence.

---

## Repository Tree

```
airledger/
├── .github/workflows/ci.yml
├── .editorconfig  .gitignore  .env.example  .pre-commit-config.yaml
├── Dockerfile  Makefile  pyproject.toml  requirements.txt  requirements-dev.txt
├── README.md  ARCHITECTURE.md  SECURITY.md
├── docs/ (EVALUATION.md, ASSUMPTIONS.md, DEMO_SCRIPT.md)
├── app/
│   ├── __init__.py  main.py  config.py  constants.py  errors.py
│   ├── api/       (routes.py, schemas.py, middleware.py, deps.py)
│   ├── services/  (plan_service.py, simulate_service.py, home_service.py,
│   │               community_service.py, assistant_service.py)
│   ├── engine/    (models.py, exposure.py, ventilation.py, indoor_sources.py,
│   │               interventions.py, ranking.py, community.py, safety_rules.py)
│   ├── data/      (air_client.py, cache.py, sample_data.json)
│   └── ai/        (provider.py, prompts.py, fallback.py, validator.py, guards.py)
├── static/ (index.html, styles.css, i18n/en.json, i18n/hi.json,
│            js/main.js api.js state.js a11y.js i18n.js render/)
└── tests/  (conftest.py, unit/, integration/, a11y/, js/)
```

---

## Quality Tooling & Verification

Run the complete verification pipeline with one command:
```bash
make check
```

Or run individual verification targets:
- `make lint`: Enforces curated ruff rules across `app` and `tests`
- `make format`: Auto-formats Python code with ruff
- `make typecheck`: Runs strict `mypy` type checking across all `app/` modules
- `make security`: Runs `bandit` static analysis and `pip-audit` vulnerability scanning
- `make complexity`: Validates low cyclomatic complexity (`radon cc app -n C`) and high maintainability (`radon mi app -n B`)
- `make jslines`: Verifies all vanilla JS modules remain under the 200-line budget limit
- `make test`: Runs `pytest` with coverage report (`--cov=app`, fail under 90%)
- `make jstest`: Runs frontend test suite with native `node --test tests/js/*.test.js`
- `make run`: Starts local server at `http://127.0.0.1:8000`
- `make docker`: Builds slim production Docker container

---

## Architecture & Purity Invariants

1. **One-way import hierarchy:**
   `app/api -> app/services -> app/engine, app/data, app/ai`. The `engine` package imports nothing from other `app` packages. `ai` imports `engine.models` only. `data` imports nothing from `engine` or `ai`.
2. **Pure domain calculations:**
   `app/engine` is strictly deterministic with zero I/O, no network calls, no globals, no `datetime.now()`, and no `random`.
3. **No magic numbers:**
   All domain constants, conversion factors, and safety thresholds reside in `app/constants.py` as typed, commented constants with units and provenance.
4. **Guarded GenAI boundaries:**
   LLM generation is restricted to structural template placeholders (e.g. `{{index_after}}`, `{{dose_saved}}`). Calculated numbers and facts are computed server-side and safely substituted; the LLM cannot hallucinate domain metrics. Medical red-flag symptom screening overrides planner recommendations and prompts immediate clinical triage.
5. **No framework/bundler bloat:**
   The frontend runs on vanilla ECMAScript modules with zero build step, zero committed `node_modules`, and strict zero-`innerHTML` DOM creation.
