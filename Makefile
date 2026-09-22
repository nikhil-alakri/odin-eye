.PHONY: help install install-browser test lint format run-api clean

help:
	@echo "Ethical AI Web Crawler commands:"
	@echo "  make install         Install package and dev dependencies in .venv"
	@echo "  make install-browser Install playwright and browser binaries"
	@echo "  make test            Run pytest suite"
	@echo "  make lint            Run ruff linting"
	@echo "  make format          Run ruff code formatter"
	@echo "  make run-api         Start the FastAPI web server & UI dashboard"
	@echo "  make clean           Clean cache files"

install:
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

install-browser:
	.venv/bin/pip install -e ".[browser]"
	.venv/bin/playwright install chromium

test:
	.venv/bin/pytest -v

lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .

run-api:
	.venv/bin/python -m ethical_crawler.cli serve --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info

