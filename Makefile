.PHONY: help install test clean

help:
	@echo "Available commands:"
	@echo "  make install   Install dependencies"
	@echo "  make test      Run test suite"
	@echo "  make clean     Clean temporary caches and artifacts"

install:
	uv sync --extra dev

test:
	uv run pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
