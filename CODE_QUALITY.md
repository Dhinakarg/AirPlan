# Code Quality Manifest — AirPlan

AirPlan enforces strict static analysis, modular size ceilings, zero mutable module globals, and deterministic physical modeling across the entire repository.

## 1. Architectural Layer Boundaries

| Layer | Directory | Responsibilities & Constraints |
| :--- | :--- | :--- |
| **Pure Physical Engine** | `app/engine/` | Deterministic exposure dose, ventilation windows, source diagnostics, intervention ranking, and clinical red-flag screening. Zero I/O, zero globals, zero `datetime.now()` or `random`. |
| **Atmospheric Data** | `app/data/` | Open-Meteo HTTP client with retry/timeout, coordinate rounding, injected `AirCache` (`TTLCache`), and offline `sample_data.json` fallback. |
| **Guarded AI Layer** | `app/ai/` | Prompt injection sanitization, `{{placeholder}}`-only JSON validation, zero-naked-digit AST/regex guard, and safe `TemplateProvider` fallback on HTTP or SDK errors. |
| **Application Services** | `app/services/` | Orchestrates engine + data + AI and manages bounded `PledgeStore` with dependency injection. |
| **API & Middleware** | `app/api/` | Strict Pydantic schemas (`extra="forbid"`), injected `RateLimiter`, CSP, 100 KB request limit, and correlation IDs. |
| **Vanilla ES Frontend** | `static/` | Native ES modules and split CSS stylesheets; zero `innerHTML`, zero build step, CSP-compliant. |

## 2. Static Analysis & Complexity Budgets

All gates run via `make check` and are enforced in GitHub Actions CI:

* **Linter & Formatter (`ruff`)**: Enforces `E`, `F`, `I`, `B`, `UP`, `S`, `C90` (`max-complexity = 7`), `D` (Google docstrings), `ANN` (100% annotations), `SIM`, `PL`, and `RUF` with **0 `noqa` suppressions**.
* **Strict Type Checking (`mypy --strict`)**: Zero errors across all `app/` and `tests/` files with **0 `type: ignore` suppressions**.
* **Cyclomatic Complexity (`radon cc`)**: Zero blocks at Rank C or worse (`radon cc app tests -n C`).
* **Maintainability Index (`radon mi`)**: 100% Grade A across all modules (`radon mi app tests -n B`).
* **Security Auditing**: `bandit -r app -ll -s B101` (0 issues, 0 `#nosec`) and `pip-audit -r requirements.txt` (0 CVEs).

## 3. Modular File-Size Budgets

Automated CI checks enforce strict line limits across all source directories:

* **Backend Python (`app/**/*.py`)**: $\le 200$ lines per file.
* **Stylesheets (`static/css/*.css`)**: $\le 200$ lines per file.
* **Frontend JavaScript (`static/js/**/*.js`)**: $\le 150$ lines per file.
