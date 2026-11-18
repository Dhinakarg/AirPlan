.PHONY: install lint format typecheck security complexity jslines test jstest check run docker

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

complexity:
	radon cc app -n C
	radon mi app -n B

jslines:
	python -c "import glob, sys; files = sorted(glob.glob('static/js/**/*.js', recursive=True)); [print(len(open(f, encoding='utf-8').readlines()), f) for f in files]; over = [f for f in files if len(open(f, encoding='utf-8').readlines()) > 200]; sys.exit(1) if over else None"

test:
	pytest --cov=app

jstest:
	node --test tests/js/*.test.js

check: lint typecheck security complexity jslines test jstest
	@echo "All quality and safety checks passed cleanly!"

run:
	uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

docker:
	docker build -t airplan:latest .
