"""Protocolo de validacion — CTRL-02 (anti fuga de datos).

Dos riesgos distintos, dos controles distintos:
  1. Fuga por variable: incluir el objetivo o sus componentes entre los
     predictores. Se resuelve con la lista de exclusiones declarada.
  2. Fuga por particion: registros de un mismo establecimiento en
     entrenamiento y validacion. Se resuelve con GroupKFold sobre el RBD.

La evaluacion fuera de bolsa (out-of-bag) queda descartada: el muestreo con
reemplazo opera por fila y rompe la agrupacion requerida.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNAS_OBJETIVO = ["EFECTIVR", "SUPERAR", "INICIAR", "MEJORAR", "INTEGRAR", "IGUALDR", "SEL", "INDICER"]
COLUMNA_GRUPO = "rbd"


class FugaDeDatos(AssertionError):
    """Se detecto informacion del objetivo entre los predictores."""


def verificar_exclusion_objetivo(columnas: list[str], objetivo: str) -> None:
    prohibidas = {c for c in COLUMNAS_OBJETIVO if c != objetivo} | {objetivo}
    intrusas = prohibidas.intersection(columnas)
    if intrusas:
        raise FugaDeDatos(
            f"Variables objetivo presentes entre los predictores: {sorted(intrusas)}. "
            "CTRL-02 bloquea el entrenamiento."
        )


def particiones_agrupadas(df: pd.DataFrame, n_particiones: int = 5, columna_grupo: str = COLUMNA_GRUPO):
    """GroupKFold por establecimiento. Devuelve un generador de (train, test)."""
    from sklearn.model_selection import GroupKFold

    if columna_grupo not in df.columns:
        raise KeyError(f"No existe la columna de agrupacion '{columna_grupo}'.")
    gkf = GroupKFold(n_splits=n_particiones)
    return gkf.split(df, groups=df[columna_grupo])


def verificar_particion_limpia(df: pd.DataFrame, idx_train, idx_test, columna_grupo: str = COLUMNA_GRUPO) -> None:
    grupos_train = set(df.iloc[idx_train][columna_grupo])
    grupos_test = set(df.iloc[idx_test][columna_grupo])
    interseccion = grupos_train & grupos_test
    if interseccion:
        raise FugaDeDatos(
            f"{len(interseccion)} establecimientos coexisten en entrenamiento y validacion."
        )


def predictor_trivial(y_train: np.ndarray, n_test: int) -> np.ndarray:
    """Referencia obligatoria: su R2 debe ser ~0. Si no lo es, hay fuga."""
    return np.full(n_test, float(np.mean(y_train)))
