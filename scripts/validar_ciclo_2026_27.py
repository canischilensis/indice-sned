"""Validacion temporal: predecir un ciclo que el modelo nunca vio.

## Que hace distinto a todo lo anterior

Cada medicion previa de este proyecto parte los mismos datos en entrenamiento y
prueba. Eso controla el sobreajuste, pero no responde la pregunta que un
sostenedor haria: **¿sirve para el proximo ciclo?**

Aqui el conjunto de prueba es un ciclo completo, posterior, obtenido despues de
que el modelo fue construido: el SNED 2026-2027, entregado por Ley de
Transparencia. Ningun establecimiento de ese ciclo participo del entrenamiento,
y tampoco lo hizo su ventana de medicion.

## Alineacion temporal, tomada de la fuente oficial

El documento de fuentes del SNED 2026-2027 declara que el ciclo se alimenta de
SIMCE 2023 y 2024 —4o basico, 6o basico y 2o medio; **8o basico no se usa**—.
Por eso:

    entrenamiento : ciclos 2020-21, 2022-23 y 2024-25   con SIMCE 2018-19
    validacion    : ciclo   2026-27                     con SIMCE 2023-24

La ventana de medicion no se elige por conveniencia: se toma de la tabla de
fuentes del propio organismo.

## Por que se reentrena aqui en vez de cargar el artefacto

El artefacto guardado se construyo con una preparacion de matriz que vive dentro
de un cuaderno. Reproducirla a mano para el ciclo nuevo introduciria diferencias
imposibles de auditar, y cualquier caida de desempeno seria indistinguible de un
error de preparacion. Entrenar aqui, con la misma funcion para ambos conjuntos,
elimina esa duda: lo unico que cambia entre entrenamiento y prueba es el ciclo.

## Las dos preguntas que responde

  1. ¿Cuanto se degrada la estimacion del indice en un ciclo futuro?
  2. ¿Acierta quien recibe el beneficio, que es la consecuencia monetaria?

La segunda importa mas. Un modelo puede estimar bien el nivel y equivocarse en
la frontera, que es donde se decide el dinero.

## Uso

    python scripts/validar_ciclo_2026_27.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "processed"

CICLOS_ENTRENAMIENTO = ["2020-21", "2022-23", "2024-25"]
CICLO_VALIDACION = "2026-27"
BIENIO_ENTRENAMIENTO = "2018-19"
BIENIO_VALIDACION = "2023-24"

#: 8o basico queda fuera a proposito: la tabla de fuentes oficial del ciclo
#: 2026-2027 no lo incluye. Conservarlo obligaria a imputarlo entero y meteria
#: ruido con apariencia de dato.
SIMCE = [
    "simce_lect_4b", "simce_mate_4b",
    "simce_lect_6b", "simce_mate_6b",
    "simce_lect_2m", "simce_mate_2m",
]
CONTEXTO = ["ES_RURAL", "CLUSTER"]
SELECCIONADO = {"1", "2"}
SEMILLA = 42


def _llave(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.lstrip("0")


def _armar(sned: pd.DataFrame, simce: pd.DataFrame, ciclo: str, bienio: str) -> pd.DataFrame:
    izquierda = sned[sned["BIENIO_PREMIO"].astype(str) == ciclo].copy()
    derecha = simce[simce["BIENIO"].astype(str) == bienio].copy()
    izquierda["_llave"] = _llave(izquierda["RBD"])
    derecha["_llave"] = _llave(derecha["rbd"])

    columnas = ["_llave"] + [c for c in SIMCE if c in derecha.columns]
    unido = izquierda.merge(derecha[columnas].drop_duplicates("_llave"), on="_llave", how="left")
    cruzados = unido[SIMCE[0]].notna().sum() if SIMCE[0] in unido else 0
    print(
        f"  {ciclo:<8} con SIMCE {bienio}: {len(unido):>6} establecimientos, "
        f"{cruzados:>6} con medicion ({cruzados / max(len(unido), 1):.1%})"
    )
    return unido


def _matriz(datos: pd.DataFrame, medianas: pd.Series | None) -> tuple[pd.DataFrame, pd.Series]:
    """Misma preparacion para entrenamiento y validacion. Sin excepciones.

    Las medianas de imputacion se calculan UNA vez, sobre el entrenamiento, y se
    aplican al ciclo de validacion. Calcularlas sobre el conjunto de prueba seria
    dejar que el futuro informe sobre si mismo.
    """
    X = pd.DataFrame(index=datos.index)
    for columna in SIMCE:
        valores = pd.to_numeric(datos.get(columna), errors="coerce")
        X[f"{columna}_ausente"] = valores.isna().astype(int)
        X[columna] = valores
    for columna in CONTEXTO:
        X[columna] = pd.to_numeric(datos.get(columna), errors="coerce")

    if medianas is None:
        medianas = X[SIMCE + CONTEXTO].median()
    X[SIMCE + CONTEXTO] = X[SIMCE + CONTEXTO].fillna(medianas)
    return X, medianas


def main() -> int:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score

    print("=" * 66)
    print("Validacion temporal: el ciclo 2026-27, que el modelo nunca vio")
    print("=" * 66 + "\n")

    sned = pd.read_parquet(PROCESADO / "sned_maestro_ciclos.parquet")
    simce = pd.read_parquet(PROCESADO / "simce_maestro_bienios.parquet")
    print(f"Maestro SNED : {len(sned)} filas, ciclos {sorted(sned['BIENIO_PREMIO'].unique())}")
    print(f"Maestro SIMCE: {len(simce)} filas, bienios {sorted(simce['BIENIO'].unique())}\n")

    if CICLO_VALIDACION not in set(sned["BIENIO_PREMIO"].astype(str)):
        raise SystemExit(f"El maestro no contiene {CICLO_VALIDACION}. Corre antes el cuaderno 02_01.")

    print("1. Alineando cada ciclo con su ventana de medicion oficial")
    entrenamiento = pd.concat(
        [_armar(sned, simce, ciclo, BIENIO_ENTRENAMIENTO) for ciclo in CICLOS_ENTRENAMIENTO],
        ignore_index=True,
    )
    validacion = _armar(sned, simce, CICLO_VALIDACION, BIENIO_VALIDACION)

    entrenamiento = entrenamiento[entrenamiento["INDICER"].notna()]
    validacion = validacion[validacion["INDICER"].notna()]

    solapados = set(entrenamiento["_llave"]) & set(validacion["_llave"])
    print(
        f"\n  Establecimientos presentes en ambos conjuntos: {len(solapados)}"
        "\n  No es fuga: es el mismo colegio en anios distintos, con mediciones"
        "\n  distintas y un resultado distinto. Lo que no se repite es la observacion."
    )

    print("\n2. Entrenando con los ciclos anteriores")
    X_entrena, medianas = _matriz(entrenamiento, None)
    y_entrena = entrenamiento["INDICER"].astype(float)
    X_valida, _ = _matriz(validacion, medianas)
    y_valida = validacion["INDICER"].astype(float)
    print(f"  Entrenamiento: {len(X_entrena)} filas x {X_entrena.shape[1]} variables")
    print(f"  Validacion   : {len(X_valida)} filas")

    modelo = RandomForestRegressor(
        n_estimators=300, max_depth=10, random_state=SEMILLA, n_jobs=-1
    )
    modelo.fit(X_entrena, y_entrena)
    estimado = modelo.predict(X_valida)

    print("\n3. Estimacion del indice en el ciclo no visto\n")
    r2 = r2_score(y_valida, estimado)
    mae = mean_absolute_error(y_valida, estimado)
    r2_dentro = r2_score(y_entrena, modelo.predict(X_entrena))
    trivial = mean_absolute_error(y_valida, np.full_like(y_valida, y_entrena.mean()))

    print(f"  {'R2 sobre el propio entrenamiento':<42} {r2_dentro:>8.4f}")
    print(f"  {'R2 sobre el ciclo 2026-27':<42} {r2:>8.4f}")
    print(f"  {'MAE sobre el ciclo 2026-27':<42} {mae:>8.3f}")
    print(f"  {'MAE de predecir siempre la media':<42} {trivial:>8.3f}")
    print(f"\n  Mejora sobre la prediccion trivial: {(1 - mae / trivial):.1%}")

    print("\n4. Acierto en la seleccion: quien recibe el beneficio\n")
    tabla = validacion.copy()
    tabla["_estimado"] = estimado
    tabla = tabla[tabla["SEL"].notna() & tabla["CLUSTER"].notna()]
    tabla["_real"] = tabla["SEL"].astype(str).str.strip().isin(SELECCIONADO)

    # Para cada Grupo Homogeneo se toma el numero REAL de premiados y se pregunta
    # si el modelo habria elegido a los mismos. No se replica la regla legal de
    # seleccion por matricula acumulada: su error propio se confundiria con el
    # error del modelo.
    marcas = []
    for _, grupo in tabla.groupby("CLUSTER"):
        cupos = int(grupo["_real"].sum())
        orden = grupo.sort_values("_estimado", ascending=False)
        marca = pd.Series(False, index=orden.index)
        if cupos:
            marca.iloc[:cupos] = True
        marcas.append(marca)
    tabla["_elegido"] = pd.concat(marcas).reindex(tabla.index)

    vp = int((tabla["_real"] & tabla["_elegido"]).sum())
    fp = int((~tabla["_real"] & tabla["_elegido"]).sum())
    fn = int((tabla["_real"] & ~tabla["_elegido"]).sum())
    vn = int((~tabla["_real"] & ~tabla["_elegido"]).sum())
    precision = vp / (vp + fp) if vp + fp else 0.0
    recuerdo = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * recuerdo / (precision + recuerdo) if precision + recuerdo else 0.0
    base = tabla["_real"].mean()

    print(f"  {'':<24}{'premiado real':>16}{'no premiado':>14}")
    print(f"  {'el modelo lo premia':<24}{vp:>16}{fp:>14}")
    print(f"  {'el modelo no lo premia':<24}{fn:>16}{vn:>14}")
    print(f"\n  Precision {precision:.4f} | Recuerdo {recuerdo:.4f} | F1 {f1:.4f}")
    print(f"  Exactitud {(vp + vn) / len(tabla):.4f} sobre {len(tabla)} establecimientos")
    print(f"  Tasa base de premiados: {base:.4f}. El modelo la supera {precision / base:.2f} veces.")
    print(
        f"\n  {fn} establecimientos premiados quedaron fuera de la estimacion."
        "\n  Ese es el costo real del error: un sostenedor que planifico sin el beneficio."
    )

    print(
        "\n  Lo que esta medicion NO dice: que el sistema pueda anticipar la"
        "\n  subvencion. La seleccion depende de como se muevan los demas del"
        "\n  grupo, y este ejercicio corre sobre un ciclo ya publicado."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
