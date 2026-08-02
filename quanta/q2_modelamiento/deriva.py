"""Verificacion bianual programada — CTRL-03 (Data Drift).

No hay orquestacion continua ni reentrenamiento automatico. Se registra una
linea base estadistica en el entrenamiento original y, en cada publicacion
bianual del MINEDUC, se contrasta la distribucion vigente contra ella. Si la
divergencia es severa se AUTORIZA -no se dispara- un ciclo de reentrenamiento
estatico: la decision permanece bajo criterio humano.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from compartido.rutas import MODEL_METADATA

ARCHIVO_LINEA_BASE = MODEL_METADATA / "linea_base_distribuciones.json"
UMBRAL_DESVIACION = 0.25  # desviaciones estandar de la media original


def registrar_linea_base(df: pd.DataFrame, variables: list[str], version_datos: str) -> Path:
    resumen = {
        "version_datos": version_datos,
        "fecha_registro": date.today().isoformat(),
        "n_observaciones": int(len(df)),
        "variables": {
            v: {
                "media": float(df[v].mean()),
                "desv": float(df[v].std()),
                "p25": float(df[v].quantile(0.25)),
                "p50": float(df[v].quantile(0.50)),
                "p75": float(df[v].quantile(0.75)),
                "pct_ausente": float(df[v].isna().mean()),
            }
            for v in variables
            if v in df.columns and pd.api.types.is_numeric_dtype(df[v])
        },
    }
    ARCHIVO_LINEA_BASE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_LINEA_BASE.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return ARCHIVO_LINEA_BASE


def contrastar(df_actual: pd.DataFrame) -> dict:
    """Compara la distribucion actual contra la linea base registrada."""
    if not ARCHIVO_LINEA_BASE.exists():
        raise FileNotFoundError(
            "No hay linea base registrada. Ejecuta registrar_linea_base() tras el entrenamiento original."
        )
    base = json.loads(ARCHIVO_LINEA_BASE.read_text(encoding="utf-8"))
    hallazgos = []
    for variable, stats in base["variables"].items():
        if variable not in df_actual.columns:
            hallazgos.append({"variable": variable, "estado": "ausente_en_fuente_actual"})
            continue
        desv = stats["desv"] or 1.0
        z = abs(float(df_actual[variable].mean()) - stats["media"]) / desv
        if z > UMBRAL_DESVIACION:
            hallazgos.append(
                {
                    "variable": variable,
                    "estado": "deriva",
                    "z": round(float(z), 3),
                    "media_base": round(stats["media"], 3),
                    "media_actual": round(float(df_actual[variable].mean()), 3),
                }
            )
    return {
        "version_base": base["version_datos"],
        "fecha_base": base["fecha_registro"],
        "n_variables_evaluadas": len(base["variables"]),
        "n_con_deriva": sum(1 for h in hallazgos if h.get("estado") == "deriva"),
        "hallazgos": hallazgos,
        "recomendacion": (
            "Autorizar reentrenamiento estatico y someterlo a la compuerta de R2"
            if any(h.get("estado") == "deriva" for h in hallazgos)
            else "Mantener el modelo vigente"
        ),
        "nota": "La decision final es humana. Este reporte es insumo del acta de decision bianual.",
    }


def resumen_legible(reporte: dict) -> str:
    lineas = [
        f"Linea base: {reporte['version_base']} ({reporte['fecha_base']})",
        f"Variables evaluadas: {reporte['n_variables_evaluadas']}",
        f"Con deriva: {reporte['n_con_deriva']}",
        f"Recomendacion: {reporte['recomendacion']}",
    ]
    for h in reporte["hallazgos"][:10]:
        if h.get("estado") == "deriva":
            lineas.append(f"  - {h['variable']}: z={h['z']} ({h['media_base']} -> {h['media_actual']})")
    return "\n".join(lineas)


def _sin_uso() -> None:  # pragma: no cover
    _ = np
