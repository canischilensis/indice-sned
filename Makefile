.PHONY: ayuda init instalar api cliente db-up db-init lint format test qa limpiar

VENV ?= $(shell [ -d env ] && echo env || echo .venv)
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

ayuda:
	@echo "indice-sned — comandos disponibles"
	@echo "  make init      Crea .venv e instala dependencias (Linux/macOS)"
	@echo "  make api       Levanta el cuanto 3 (FastAPI) en :8000"
	@echo "  make cliente   Levanta el cuanto 4 (React/Vite) en :5173"
	@echo "  make db-up     Levanta PostgreSQL via docker compose"
	@echo "  make db-init   Aplica esquemas, vistas y semillas"
	@echo "  make lint      ruff + mypy"
	@echo "  make format    black + ruff --fix"
	@echo "  make test      Suite completa de QA (datos, modelo, api)"
	@echo "  make qa        Compuerta de calidad completa (lint + test)"

init:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PY) -m ipykernel install --user --name indice-sned --display-name "indice-sned"
	@echo "Listo. Activar con: source $(VENV)/bin/activate"

api:
	$(PY) -m uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000

cliente:
	cd quanta/q4_cliente && npm run dev

db-up:
	docker compose up -d postgres

db-init:
	$(PY) scripts/inicializar_bd.py

lint:
	$(VENV)/bin/ruff check quanta tests
	$(VENV)/bin/mypy

format:
	$(VENV)/bin/black quanta tests
	$(VENV)/bin/ruff check --fix quanta tests

test:
	$(VENV)/bin/pytest

qa: lint test
	@echo "Compuerta de calidad superada."

limpiar:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache
