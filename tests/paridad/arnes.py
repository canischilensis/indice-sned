"""Ejercita todos los endpoints y congela las respuestas en disco.

    REPOSITORIO_DATOS=parquet  python tests/paridad/arnes.py baseline_parquet
    REPOSITORIO_DATOS=postgres python tests/paridad/arnes.py resultado_postgres

Cada endpoint se llama con la misma muestra fija en ambas corridas. Se guarda
la respuesta JSON y el tiempo de respuesta, para la comparacion de paridad y
para la tabla de rendimiento.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "quanta"))

from fastapi.testclient import TestClient  # noqa: E402

from tests.paridad.muestra import cargar  # noqa: E402

DESTINO = Path(__file__).parent


def _token(cliente, rbds: list[int]) -> dict:
    """Usuario auditor de desarrollo: jurisdiccion sobre toda la muestra.

    Se usa el rol AUDITOR porque el objeto de esta prueba es la paridad de
    datos entre adaptadores, no el control de acceso (que tiene su propia
    prueba). El token se emite por el endpoint real, no se falsifica.
    """
    r = cliente.post("/api/v1/auth/token",
                     data={"username": "auditor.demo", "password": "demo"})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def ejecutar(carpeta: str) -> dict:
    from q3_servicio.main import app
    from q3_servicio.repositorios import nombre_adaptador_activo
    from q3_servicio.servicios import motor

    motor._servicio = None                      # el adaptador se resuelve al construir
    muestra = cargar()
    rbds = muestra["rbds"]
    salida = DESTINO / carpeta
    salida.mkdir(parents=True, exist_ok=True)

    cliente = TestClient(app)
    cab = _token(cliente, rbds)
    resultados: dict[str, dict] = {}
    tiempos: dict[str, list[float]] = {}

    def llamar(nombre: str, metodo: str, url: str, **kw):
        t0 = time.perf_counter()
        r = cliente.request(metodo, url, headers=cab, **kw)
        ms = (time.perf_counter() - t0) * 1000
        tiempos.setdefault(nombre, []).append(ms)
        cuerpo = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        return {"status": r.status_code, "cuerpo": cuerpo}

    # 1 · listado de establecimientos
    resultados["listado"] = {"_": llamar("listado", "GET", "/api/v1/establecimientos")}

    for rbd in rbds:
        # 2 · detalle
        resultados.setdefault("detalle", {})[str(rbd)] = llamar(
            "detalle", "GET", f"/api/v1/establecimientos/{rbd}")
        # 3 · ranking intragrupo
        resultados.setdefault("ranking", {})[str(rbd)] = llamar(
            "ranking", "GET", f"/api/v1/establecimientos/{rbd}/ranking")
        # 4 · prediccion de los seis factores y del indice
        resultados.setdefault("prediccion", {})[str(rbd)] = llamar(
            "prediccion", "GET", f"/api/v1/prediccion/{rbd}")
        # 5 · alertas
        resultados.setdefault("alertas", {})[str(rbd)] = llamar(
            "alertas", "GET", f"/api/v1/prediccion/{rbd}/alertas")
        # 6 · explicacion SHAP
        resultados.setdefault("shapley", {})[str(rbd)] = llamar(
            "shapley", "GET", f"/api/v1/xai/{rbd}/shapley?factor=EFECTIVR")
        # 7 · simulacion con un ajuste de variable
        resultados.setdefault("simulacion", {})[str(rbd)] = llamar(
            "simulacion", "POST", "/api/v1/xai/simular",
            json={"rbd": str(rbd), "variable": "simce_mate_4b", "n_puntos": 9})

    (salida / "respuestas.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False, sort_keys=True, default=str), encoding="utf-8")
    resumen = {
        "adaptador": nombre_adaptador_activo(),
        "n_rbd": len(rbds),
        "endpoints": sorted(resultados),
        "tiempos_ms": {k: {"n": len(v), "media": round(sum(v)/len(v), 1),
                           "max": round(max(v), 1)} for k, v in tiempos.items()},
    }
    (salida / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    r = ejecutar(sys.argv[1] if len(sys.argv) > 1 else "salida")
    print(json.dumps(r, indent=2, ensure_ascii=False))
