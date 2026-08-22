"""Construye la fila de insumos del ciclo 2026-2027 para cada establecimiento.

## Que problema resuelve

La tabla analitica del proyecto llega hasta el ciclo 2024-25. El resultado
oficial del 2026-2027 ya esta ingestado, pero sin insumos no hay estimacion: la
aplicacion puede mostrar el indice publicado y no puede predecir nada sobre ese
ciclo, ni servir de base para el siguiente.

Este guion arma esa fila.

## De donde sale cada bloque, y que se arrastra

La tabla de fuentes oficial del ciclo declara que se alimenta de SIMCE 2023 y
2024, IDPS 2023 y 2024, rendimiento 2023-2024, matricula 2024-2025, dotacion
2024-2025 e IVE 2024-2025.

| Bloque | Origen | Estado |
|---|---|---|
| SIMCE, 8 variables | `simce_maestro_bienios`, bienio 2023-24 | Dato real del ciclo |
| IDPS | `idps_maestro_bienios`, bienio 2024-25 | Dato real, ventana aproximada |
| Identidad y contexto | `sned_maestro_ciclos`, ciclo 2026-27 | Dato real del ciclo |
| Resto: matricula, IVE, SEP, dotacion, denuncias, procesos, tasas | Ciclo anterior del mismo establecimiento | **Arrastrado** |

**El arrastre se declara y no se disimula.** Las fuentes crudas de esas
variables existen para 2024 y 2025, pero su normalizacion vive en los cuadernos
de ingesta y reprocesarla completa excede lo que se puede verificar en el plazo
disponible. Arrastrar el ultimo valor conocido es un supuesto explicito —que
esas variables cambian poco entre ciclos consecutivos— y el guion informa
cuantas filas lo usan.

Dos fuentes no se pueden arrastrar ni reprocesar porque **no existen** para la
ventana: los procesos administrativos de la Superintendencia entre julio de 2023
y junio de 2025, y las mediaciones posteriores a 2023. Alimentan Mejoramiento
(2 %) y parte de Igualdad.

## Que produce

`data/processed/tabla_modelo_ciclos.parquet`: la tabla analitica original mas
las filas del ciclo nuevo, con el mismo esquema. **No sobrescribe** la tabla de
entrenamiento: el adaptador de datos la prefiere si existe, y si se borra el
sistema vuelve al comportamiento anterior.

## Uso

    python scripts/construir_insumos_2026_27.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "processed"

CICLO = "2026-27"
BIENIO_SIMCE = "2023-24"
BIENIO_IDPS = "2024-25"

SIMCE = [
    "simce_lect_4b", "simce_mate_4b",
    "simce_lect_6b", "simce_mate_6b",
    "simce_lect_8b", "simce_mate_8b",
    "simce_lect_2m", "simce_mate_2m",
]

#: Columnas que vienen del resultado oficial del ciclo y no se arrastran nunca.
DEL_CICLO = [
    "NOM_RBD", "CLUSTER", "ES_RURAL", "cod_depe2",
    "EFECTIVR", "SUPERAR", "INICIAR", "MEJORAR", "INTEGRAR", "IGUALDR",
    "INDICER", "SEL",
]


def _llave(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    print("=" * 66)
    print(f"Insumos del ciclo {CICLO}")
    print("=" * 66 + "\n")

    analitica = pd.read_parquet(PROCESADO / "tabla_modelo_largo.parquet")
    sned = pd.read_parquet(PROCESADO / "sned_maestro_ciclos.parquet")
    simce = pd.read_parquet(PROCESADO / "simce_maestro_bienios.parquet")
    idps = pd.read_parquet(PROCESADO / "idps_maestro_bienios.parquet")

    ciclos = set(analitica["BIENIO_PREMIO"].astype(str))
    print(f"Tabla analitica actual : {len(analitica)} filas, ciclos {sorted(ciclos)}")
    if CICLO in ciclos:
        print(f"\nEl ciclo {CICLO} ya esta en la tabla analitica. No hay nada que construir.")
        return 0

    oficial = sned[sned["BIENIO_PREMIO"].astype(str) == CICLO].copy()
    if oficial.empty:
        raise SystemExit(f"El maestro SNED no contiene el ciclo {CICLO}. Corre antes el cuaderno 02_01.")
    oficial["_llave"] = _llave(oficial["RBD"])
    print(f"Resultado oficial {CICLO}: {len(oficial)} establecimientos\n")

    print("1. Bloques con dato real del ciclo")

    fuente_simce = simce[simce["BIENIO"].astype(str) == BIENIO_SIMCE].copy()
    fuente_simce["_llave"] = _llave(fuente_simce["rbd"])
    cols_simce = ["_llave"] + [c for c in SIMCE if c in fuente_simce.columns]
    base = oficial.merge(fuente_simce[cols_simce].drop_duplicates("_llave"), on="_llave", how="left")
    con_simce = int(base[SIMCE[0]].notna().sum()) if SIMCE[0] in base else 0
    print(f"  SIMCE {BIENIO_SIMCE}: {con_simce} de {len(base)} con medicion ({con_simce / len(base):.1%})")

    fuente_idps = idps[idps["BIENIO"].astype(str) == BIENIO_IDPS].copy()
    fuente_idps["_llave"] = _llave(fuente_idps["rbd"])
    cols_idps = [c for c in fuente_idps.columns if c.startswith("idps_")]
    base = base.merge(
        fuente_idps[["_llave", *cols_idps]].drop_duplicates("_llave"), on="_llave", how="left"
    )
    if cols_idps:
        con_idps = int(base[cols_idps[0]].notna().sum())
        print(f"  IDPS  {BIENIO_IDPS}: {con_idps} de {len(base)} con medicion ({con_idps / len(base):.1%})")

    print("\n2. Bloque arrastrado del ciclo anterior")
    analitica = analitica.copy()
    analitica["_llave"] = _llave(analitica["rbd"])
    previo = (
        analitica.sort_values("BIENIO_PREMIO").drop_duplicates("_llave", keep="last").set_index("_llave")
    )

    ya_resueltas = set(base.columns) | {"rbd", "BIENIO_PREMIO", "_llave"} | set(DEL_CICLO)
    arrastrables = [c for c in analitica.columns if c not in ya_resueltas]
    for columna in arrastrables:
        base[columna] = base["_llave"].map(previo[columna])

    con_arrastre = int(base["_llave"].isin(previo.index).sum())
    print(f"  {len(arrastrables)} variables arrastradas desde el ciclo anterior")
    print(f"  {con_arrastre} de {len(base)} establecimientos tienen ciclo previo ({con_arrastre / len(base):.1%})")
    print(f"  {len(base) - con_arrastre} quedan sin esas variables: son RBD nuevos o reabiertos")

    print("\n3. Armando la fila del ciclo")
    base["rbd"] = base["RBD"].astype(str).str.strip()
    base["BIENIO_PREMIO"] = CICLO
    base["insumos_arrastrados"] = base["_llave"].isin(previo.index)

    faltantes = [c for c in analitica.columns if c not in base.columns and c != "_llave"]
    for columna in faltantes:
        base[columna] = pd.NA

    columnas = [c for c in analitica.columns if c != "_llave"]
    nuevas = base[[*columnas, "insumos_arrastrados"]]

    completa = pd.concat(
        [analitica.drop(columns=["_llave"]).assign(insumos_arrastrados=False), nuevas],
        ignore_index=True,
    )

    destino = PROCESADO / "tabla_modelo_ciclos.parquet"
    completa.to_parquet(destino, index=False)
    print(f"  Escrito: {destino.relative_to(RAIZ)}")
    print(f"  {len(completa)} filas, ciclos {sorted(set(completa['BIENIO_PREMIO'].astype(str)))}")

    print("\n4. Lo que queda declarado")
    print("  · Los procesos administrativos de julio 2023 a junio 2025 NO existen entre las")
    print("    fuentes descargadas. Alimentan Mejoramiento (2 %) y parte de Igualdad.")
    print("  · Las mediaciones llegan hasta 2023.")
    print("  · Las variables arrastradas son un supuesto declarado, no dato del ciclo.")
    print("  · Las ocho diferencias SIMCE siguen sin materializarse: el motor las imputa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
