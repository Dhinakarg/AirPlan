# Contributing to AirPlan

## Setup
1. Virtual environment: `python -m venv .venv`
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Node.js (>=18) is required for frontend test execution.

## Verification
Run all linters, type checks, security scanners, and test suites:
```bash
make check
```

## Commit Style
Follow Conventional Commits format with imperative summaries:
- `feat: <summary>`
- `fix: <summary>`
- `refactor: <summary>`
- `docs: <summary>`
