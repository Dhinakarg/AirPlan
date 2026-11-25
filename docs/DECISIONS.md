# Architecture Decision Records (ADRs) — AirPlan

## ADR-001: Deterministic Python Engine Separated from GenAI
* **Context**: Generative models hallucinate numeric concentrations, exposure reductions, and medical claims during health-critical air pollution advisories.
* **Decision**: Isolate all physical exposure math, ventilation window detection, and cost-benefit ranking in a pure Python engine (`app/engine/`) with zero I/O. Restrict `app/ai/` to generating narrative templates containing `{{placeholder}}` tokens validated against `ALLOWED_PLACEHOLDERS` and substituted server-side with engine-computed metrics.
* **Consequence**: Numerical outputs are 100% reproducible and property-tested via Hypothesis; LLM or SDK failures gracefully fall back to deterministic templates without returning HTTP 500.

## ADR-002: Dependency-Injected State Stores Instead of Module Globals
* **Context**: Module-level mutable dicts and lists complicate test isolation, concurrency reasoning, and static quality analysis.
* **Decision**: Encapsulate rate-limiting timestamps in `RateLimiter` (`app/api/middleware.py`), atmospheric caching in `AirCache` (`app/data/cache.py`), and community pledges in `PledgeStore` (`app/services/community_service.py`), each supporting explicit injection.
* **Consequence**: Zero module-level mutable collections in `app/`, deterministic unit tests, and clean lifecycle management.

## ADR-003: Zero-Build Vanilla ES Modules & Strict CSP
* **Context**: Heavy frontend build toolchains add supply-chain surface area and complicate offline/fresh-clone execution.
* **Decision**: Use native browser ES modules (`static/js/`) and split CSS stylesheets (`static/css/`) with `el()` DOM helpers (`textContent` only, zero `innerHTML`). Enforce modular size limits ($\le 150$ lines JS, $\le 200$ lines CSS) and strict Content Security Policy headers.
* **Consequence**: Instant zero-setup startup with `uvicorn`, 100% Lighthouse Accessibility score, and zero npm supply-chain CVEs.

## ADR-004: Bilingual Clinical Red-Flag Override
* **Context**: Users experiencing acute respiratory or cardiac emergencies (e.g., chest pain, severe dyspnea, cyanosis) must not be routed to routine environmental planning.
* **Decision**: Screen incoming queries deterministically in English and Hindi (`app/engine/safety_rules.py`) before any AI invocation, with negation awareness to avoid false positives.
* **Consequence**: Immediate emergency clinical triage directive (`112`/`102`) with zero LLM latency or override risk.

