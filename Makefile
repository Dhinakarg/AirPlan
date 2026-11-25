.PHONY: install lint format typecheck security complexity jslines test jstest check run docker samples

install:
	pip install -r requirements-dev.txt

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

typecheck:
	mypy --strict app tests

security:
	bandit -r app -ll -s B101
	pip-audit -r requirements.txt

complexity:
	radon cc app tests -n C
	radon mi app tests -n B

jslines:
	python -c "import glob, sys; css = [f for f in glob.glob('static/css/*.css') if len(open(f, encoding='utf-8').readlines()) > 200]; js = [f for f in glob.glob('static/js/**/*.js', recursive=True) if len(open(f, encoding='utf-8').readlines()) > 150]; sys.exit(1) if css or js else None"

test:
	pytest --cov=app

jstest:
	node --test tests/js/*.test.js

samples:
	python scripts/generate_samples.py

check: lint typecheck security complexity jslines test jstest
	@echo "All quality and safety checks passed cleanly!"

run:
	uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

docker:
	docker build -t airplan:latest .
