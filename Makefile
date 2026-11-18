.PHONY: install lint format typecheck security test jstest check run docker

install:
	pip install -r requirements-dev.txt

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

typecheck:
	mypy --strict app

security:
	bandit -r app -ll -s B101
	pip-audit -r requirements.txt

test:
	pytest --cov=app

jstest:
	node --test tests/js/*.test.js

check: lint typecheck security test jstest
	@echo "All quality and safety checks passed cleanly!"

run:
	uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

docker:
	docker build -t airledger:latest .
