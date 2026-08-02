"""Muestra fija y reproducible para la comparacion de adaptadores.

La semilla es fija: los mismos 20 RBD en ambas corridas, siempre. Se incluyen
deliberadamente cuatro casos borde declarados, porque un muestreo puramente
aleatorio puede no tocarlos y son justo donde los dos adaptadores podrian
divergir.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVO = Path(__file__).parent / "muestra.json"
SEMILLA = 20260802
N_ALEATORIOS = 16


def construir() -> dict:
    """Selecciona la muestra desde PostgreSQL y la congela en muestra.json."""
    import os

    from sqlalchemy import create_engine, text

    eng = create_engine(os.environ["DATABASE_URL"], future=True)
    with eng.connect() as cx:
        def uno(sql: str) -> int | None:
            r = cx.execute(text(sql)).scalar()
            return int(r) if r is not None else None

        bordes = {
            "sin_medicion_2m": uno("""
                SELECT ce.rbd FROM core.conjunto_entrenamiento ce
                WHERE NOT EXISTS (SELECT 1 FROM hechos.simce_medicion s
                                  WHERE s.rbd=ce.rbd AND s.nivel_cod='2m')
                ORDER BY ce.rbd LIMIT 1"""),
            "rural": uno("""
                SELECT ce.rbd FROM core.conjunto_entrenamiento ce
                JOIN core.establecimiento_periodo ep ON ep.rbd=ce.rbd
                WHERE ep.es_rural ORDER BY ce.rbd LIMIT 1"""),
            "cambia_cluster": uno("""
                SELECT rbd FROM (
                  SELECT sr.rbd, COUNT(DISTINCT sr.cluster_codigo) n
                  FROM hechos.sned_resultado sr
                  JOIN core.periodo p ON p.periodo_id=sr.periodo_id
                  JOIN core.conjunto_entrenamiento ce ON ce.rbd=sr.rbd
                  WHERE p.tipo='CICLO_SNED' AND p.etiqueta IN ('2020-21','2022-23','2024-25')
                  GROUP BY sr.rbd) t
                WHERE n>1 ORDER BY rbd LIMIT 1"""),
            "sel_tramo_100": uno("""
                SELECT sr.rbd FROM hechos.sned_resultado sr
                JOIN core.conjunto_entrenamiento ce ON ce.rbd=sr.rbd
                WHERE sr.sel=1 ORDER BY sr.rbd LIMIT 1"""),
        }
        universo = [int(r[0]) for r in cx.execute(text(
            "SELECT rbd FROM core.conjunto_entrenamiento ORDER BY rbd")).all()]

    rnd = random.Random(SEMILLA)
    fijos = [v for v in bordes.values() if v is not None]
    resto = [r for r in universo if r not in fijos]
    aleatorios = rnd.sample(resto, N_ALEATORIOS)

    datos = {
        "semilla": SEMILLA,
        "bordes": bordes,
        "rbds": sorted(fijos + aleatorios),
    }
    ARCHIVO.write_text(json.dumps(datos, indent=2), encoding="utf-8")
    return datos


def cargar() -> dict:
    if not ARCHIVO.exists():
        return construir()
    return json.loads(ARCHIVO.read_text(encoding="utf-8"))


if __name__ == "__main__":
    d = construir()
    print(f"semilla {d['semilla']} | {len(d['rbds'])} RBD")
    for k, v in d["bordes"].items():
        print(f"  borde {k:<18} -> RBD {v}")
