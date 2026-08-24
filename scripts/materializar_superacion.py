"""Persiste la diferencia SIMCE corregida por significancia, ciclo por ciclo.

## Que corrige

El motor espera ocho variables `dif_simce_*` que nunca se persistieron: se
calculaban en el cuaderno de entrenamiento como `actual - previo`, cruda, y al
servir se imputaban por mediana. Eso produce dos defectos a la vez:

  1. **Metodologico.** El metodo oficial no usa la resta cruda:

     > "Las diferencias corregidas por significancia corresponden a las
     > diferencias reportadas estandarizadas, en los casos en que estas sean
     > significativas estadisticamente, y se consideran nulas en los casos en
     > que el SIMCE reporta las diferencias como no significativas."
     > -- MINEDUC, Documento Tecnico SNED 2026-2027, p. 12

     Medido sobre el dato del proyecto: **el 69,8 % de las diferencias no es
     significativa** y por lo tanto vale cero. El entrenamiento anterior le
     entrego ruido estadistico al modelo en dos de cada tres establecimientos.

  2. **De ingenieria.** Al no persistirse, la variable no llega al momento de
     servir y se rellena con un valor fijo. El simulador movia el puntaje y
     dejaba la variacion congelada.

## Que hace

Lee las columnas oficiales `dif_*` y `sigdif_*` de los archivos crudos del SIMCE
—no las calcula—, aplica la regla citada y escribe ocho columnas `superac_*` en
la tabla analitica, por establecimiento y por ciclo.

## Las ventanas, y cual esta documentada

| Ciclo | 4 basico | 6 basico | 8 basico | 2 medio | Respaldo |
|---|---|---|---|---|---|
| 2020-21 | 2018 | 2018 | **2017** | 2018 | Anexo 1, p. 20 |
| 2022-23 | 2018 | 2018 | **2019** | 2018 | p. 8 |
| 2024-25 | 2018 | 2018 | **2019** | 2018 | Anexo 1, p. 24 |
| 2026-27 | 2024 | 2024 | **fuera** | 2024 | Cuadro 5, p. 11 |

**Los cuatro ciclos tienen respaldo documental y ninguna ventana es supuesta.**
Los tres anteriores a la pandemia difieren entre si en 8 basico: 2017 en el
primero y 2019 en los otros dos. Es la clase de detalle que una ventana comun
—plausible y comoda— habria pasado por alto sin que nada fallara.

Dos precisiones sobre el ciclo 2026-27, ambas verificadas contra el dato: **8
basico queda fuera** porque el Cuadro 5 no lo incluye, y la diferencia de 6
basico del archivo 2024 compara contra **2018**, que es la ventana 2018-2024 que
ese mismo cuadro declara. No hay que construirla: viene publicada.

Cada ciclo informa en la salida el documento y la pagina de donde sale su
ventana. Una materializacion que no puede decir de donde saco su ventana no es
verificable.

## Uso

    python scripts/materializar_superacion.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "raw" / "simce"
PROCESADO = RAIZ / "data" / "processed"

NIVELES = ("4b", "6b", "8b", "2m")
ASIGNATURAS = ("lect", "mate")

#: Ventana de medicion de cada ciclo, tomada del Anexo 1 de su propio documento
#: tecnico. **No se comparten entre ciclos**: los tres anteriores a la pandemia
#: coinciden en 4 basico, 6 basico y 2 medio, y difieren en 8 basico, que en
#: 2020-2021 es 2017 y en los otros dos es 2019. Suponer una ventana comun
#: —como hizo la primera version de este guion— habria materializado el ciclo
#: 2020-2021 con el archivo equivocado sin que nada fallara.
VENTANAS = {
    "2020-21": (
        {
            "4b": "simce4b2018_rbd_publica_final.xlsx",
            "6b": "simce6b2018_rbd_publica_final.xlsx",
            "8b": "simce8b2017_rbd_pública_publica_final.xlsx",
            "2m": "simce2m2018_rbd_publica_final.xlsx",
        },
        "Doc. Tecnico 2020-2021, Anexo 1, p. 20 · 8 basico 2017",
    ),
    "2022-23": (
        {
            "4b": "simce4b2018_rbd_publica_final.xlsx",
            "6b": "simce6b2018_rbd_publica_final.xlsx",
            "8b": "simce8b2019_rbd.xlsx",
            "2m": "simce2m2018_rbd_publica_final.xlsx",
        },
        "Doc. Tecnico 2022-2023, p. 8 · SIMCE 2017, 2018 y 8 de 2019",
    ),
    "2024-25": (
        {
            "4b": "simce4b2018_rbd_publica_final.xlsx",
            "6b": "simce6b2018_rbd_publica_final.xlsx",
            "8b": "simce8b2019_rbd.xlsx",
            "2m": "simce2m2018_rbd_publica_final.xlsx",
        },
        "Doc. Tecnico 2024-2025, Anexo 1, p. 24 · 8 basico 2019",
    ),
    "2026-27": (
        {
            "4b": "simce4b2024_rbd_final.xlsx",
            "6b": "simce6b2024_rbd_final.xlsx",
            "2m": "simce2m2024_rbd_final.xlsx",
        },
        "Doc. Tecnico 2026-2027, Cuadro 5, p. 11 · 8 basico fuera del ciclo",
    ),
}


def _columna(df: pd.DataFrame, patron: str) -> str | None:
    regex = re.compile(patron, re.IGNORECASE)
    for c in df.columns:
        if regex.fullmatch(str(c).strip()):
            return str(c)
    return None


def _extraer(nivel: str, archivo: Path) -> pd.DataFrame | None:
    if not archivo.exists():
        print(f"    AVISO: falta {archivo.name}; el nivel {nivel} queda sin variacion.")
        return None
    crudo = pd.read_excel(archivo, dtype={"rbd": str, "RBD": str})
    llave = _columna(crudo, r"rbd")
    if llave is None:
        print(f"    AVISO: {archivo.name} no declara RBD.")
        return None

    salida = pd.DataFrame({"_llave": crudo[llave].astype(str).str.strip().str.lstrip("0")})
    hallados = 0
    for asignatura in ASIGNATURAS:
        col_dif = _columna(crudo, rf"dif_{asignatura}{nivel}(_rbd)?")
        col_sig = _columna(crudo, rf"sigdif_{asignatura}{nivel}(_rbd)?")
        if col_dif is None or col_sig is None:
            continue
        dif = pd.to_numeric(crudo[col_dif], errors="coerce")
        sig = pd.to_numeric(crudo[col_sig], errors="coerce")
        # La regla oficial, literal: la diferencia vale solo si el propio SIMCE
        # la reporto significativa; si no, vale cero. No se estima nada aqui.
        salida[f"superac_{asignatura}_{nivel}"] = np.where(sig.fillna(0) != 0, dif, 0.0)
        salida[f"superac_{asignatura}_{nivel}"] = salida[
            f"superac_{asignatura}_{nivel}"
        ].where(dif.notna())
        hallados += 1
    return salida.drop_duplicates("_llave") if hallados else None


def _insumo_de_ventana(archivos: dict[str, str]) -> pd.DataFrame:
    partes = [p for nivel, nombre in archivos.items() if (p := _extraer(nivel, CRUDO / nombre)) is not None]
    if not partes:
        return pd.DataFrame(columns=["_llave"])
    insumo = partes[0]
    for parte in partes[1:]:
        insumo = insumo.merge(parte, on="_llave", how="outer")
    return insumo


def main() -> int:
    print("=" * 68)
    print("Materializacion de la diferencia SIMCE corregida por significancia")
    print("MINEDUC, Documento Tecnico SNED 2026-2027, p. 12")
    print("=" * 68 + "\n")

    ruta = PROCESADO / "tabla_modelo_ciclos.parquet"
    if not ruta.exists():
        raise SystemExit(
            f"No existe {ruta.name}. Corre antes scripts/construir_insumos_2026_27.py"
        )
    tabla = pd.read_parquet(ruta)
    tabla["_llave"] = tabla["rbd"].astype(str).str.strip().str.lstrip("0")
    print(f"Tabla analitica: {len(tabla)} filas, ciclos {sorted(set(tabla['BIENIO_PREMIO'].astype(str)))}\n")

    columnas = [f"superac_{a}_{n}" for n in NIVELES for a in ASIGNATURAS]
    for c in columnas:
        tabla[c] = np.nan

    total_anuladas = total_validas = 0

    for ciclo, (archivos, respaldo) in VENTANAS.items():
        marca = tabla["BIENIO_PREMIO"].astype(str) == ciclo
        if not marca.any():
            continue
        print(f"{ciclo}  ({respaldo})")
        insumo = _insumo_de_ventana(archivos).set_index("_llave")
        presentes = [c for c in columnas if c in insumo.columns]
        for c in presentes:
            tabla.loc[marca, c] = tabla.loc[marca, "_llave"].map(insumo[c])

        bloque = tabla.loc[marca, presentes]
        validas = int(bloque.notna().sum().sum())
        anuladas = int((bloque == 0).sum().sum())
        total_validas += validas
        total_anuladas += anuladas
        cobertura = tabla.loc[marca, presentes].notna().any(axis=1).mean() if presentes else 0
        print(f"    {len(presentes)} variables · {cobertura:.1%} de los establecimientos con variacion")
        if validas:
            print(f"    {anuladas} de {validas} anuladas por no significativas ({anuladas / validas:.1%})\n")
        else:
            print()

    tabla = tabla.drop(columns=["_llave"])
    tabla.to_parquet(ruta, index=False)

    print("-" * 68)
    if total_validas:
        print(f"Total: {total_anuladas} de {total_validas} diferencias anuladas "
              f"({total_anuladas / total_validas:.1%})")
        print("Esa proporcion es la correccion que el metodo exige y el entrenamiento")
        print("anterior no aplicaba: ruido estadistico entregado como si fuera senal.")
    print(f"\nEscrito: {ruta.relative_to(RAIZ)}  ({len(tabla)} filas x {tabla.shape[1]} columnas)")
    print("\nLas cuatro ventanas tienen respaldo documental: ningun ciclo quedo supuesto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
