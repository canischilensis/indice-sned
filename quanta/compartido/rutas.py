"""Resolucion de rutas del proyecto. Unico lugar que conoce el layout en disco."""

from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _ruta(variable: str, defecto: str) -> Path:
    valor = os.getenv(variable, defecto)
    p = Path(valor)
    return p if p.is_absolute() else RAIZ / p


DATA_RAW = _ruta("SNED_DATA_RAW", "data/raw")
DATA_INTERIM = _ruta("SNED_DATA_INTERIM", "data/interim")
DATA_PROCESSED = _ruta("SNED_DATA_PROCESSED", "data/processed")
MODEL_REGISTRY = _ruta("SNED_MODEL_REGISTRY", "models/registry")
MODEL_METADATA = _ruta("SNED_MODEL_METADATA", "models/metadata")
CONTRATOS = RAIZ / "contratos"
