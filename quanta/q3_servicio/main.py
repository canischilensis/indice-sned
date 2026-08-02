"""Punto de entrada del cuanto 3.

    uvicorn q3_servicio.main:app --reload --app-dir quanta --port 8000

Documentacion interactiva: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from q3_servicio import __version__
from q3_servicio.api.v1.rutas import api_v1
from q3_servicio.core.config import config

cfg = config()

app = FastAPI(
    title="Indice SNED — Servicio Predictivo B2B",
    version=__version__,
    description=(
        "Encapsula el motor predictivo tras el Patron Strategy. "
        "La IA asiste; la decision estrategica la toma el equipo directivo."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1, prefix=cfg.api_prefix)


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "servicio": "indice-sned",
        "version": __version__,
        "documentacion": "/docs",
        "api": cfg.api_prefix,
    }
