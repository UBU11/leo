.PHONY: help install init-db seed crawl web dispatch test

help:
	@echo "Available commands:"
	@echo "  make install    Install dependencies and playwright browsers"
	@echo "  make init-db    Initialize SQLite database schema"
	@echo "  make seed       Ingest initial brands into database"
	@echo "  make crawl      Run crawler and classifier daemon"
	@echo "  make web        Launch FastAPI human-in-the-loop review UI"
	@echo "  make dispatch   Start outbound plain-text SMTP dispatcher"
	@echo "  make test       Run test suite"

install:
	uv sync --extra dev
	uv run playwright install chromium

init-db:
	python3 -m src.database.connection --init

seed:
	python3 -m src.ingest.seed --input data/initial_brands.csv

crawl:
	python3 -m src.scraper.crawler

web:
	uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload

dispatch:
	python3 -m src.dispatcher.smtp_client

test:
	pytest -v
