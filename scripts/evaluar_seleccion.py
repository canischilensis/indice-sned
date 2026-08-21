"""Evalua si el modelo acierta QUIEN recibe el beneficio, no solo el indice.

## Por que esta medicion es distinta de todas las anteriores

El R2 mide cuanto se aproxima la estimacion al indice. Pero el indice no es lo
que le importa a un sostenedor: lo que le importa es **si entra o no entra** al
grupo premiado, porque de eso depende la Subvencion por Desempeno de Excelencia.

Un modelo puede tener un R2 modesto y aun asi ordenar bien, que es lo unico que
la seleccion necesita. Y al reves: puede estimar bien el nivel y equivocarse
justo en la frontera, que es donde se decide el dinero. Ninguna de las dos cosas
se ve en el R2.

## Como se evalua sin implementar la regla oficial

La regla legal de seleccion no se replica aqui, a proposito. El SNED selecciona
por matricula acumulada dentro de cada Grupo Homogeneo regional, y una
implementacion aproximada de esa regla introduciria un error propio que se
confundiria con el error del modelo.

En su lugar se usa el conteo real: **para cada Grupo Homogeneo se toma cuantos
establecimientos fueron efectivamente seleccionados, y se pregunta si el modelo
habria elegido a los mismos**. Asi lo que se mide es exclusivamente la capacidad
de ordenamiento del modelo, que es su parte del problema.

## Lo que la medicion NO dice

No dice que el sistema pueda anticipar la subvencion. La seleccion depende de
como se muevan los demas establecimientos del grupo, y este ejercicio corre
sobre un ciclo ya cerrado y conocido. Es una evaluacion retrospectiva del
ordenamiento, no una promesa de resultado.

## Uso

    python scripts/evaluar_seleccion.py
    python scripts/evaluar_seleccion.py --ciclo 2024_2025
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "raw" / "sned"
PROCESADO = RAIZ / "data" / "processed"

#: 1 y 2 son seleccionados —al 25 % y al 35 %—; 3 no lo es.
SELECCIONADO = {"1", "2"}


def _leer_sned(ciclo: str) -> pd.DataFrame:
    ruta = CRUDO / f"SNED_{ciclo}.csv"
    if not ruta.exists():
        disponibles = sorted(p.name for p in CRUDO.glob("SNED_*.csv"))
        raise SystemExit(f"No existe {ruta.name}. Disponibles: {disponibles}")

    with open(ruta, encoding="latin-1") as fuente:
        primera = fuente.readline()
    separador = ";" if primera.count(";") > primera.count(",") else ","

    # Los archivos no son homogeneos entre ciclos: unos vienen con marca de orden
    # de bytes y otros no. Leerlos todos en latin-1 convierte esa marca en los
    # caracteres visibles 'i>>?' pegados al primer nombre de columna, y el
    # archivo parece no declarar RBD cuando si lo declara.
    for codificacion in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(ruta, sep=separador, encoding=codificacion, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f"No se pudo decodificar {ruta.name}.")

    # Se retira cualquier residuo no alfanumerico al inicio del nombre.
    df.columns = [re.sub(r"^[^A-Za-z0-9]+", "", str(c).strip()).upper() for c in df.columns]
    for exigida in ("RBD", "CLUSTER", "SEL", "INDICER"):
        if exigida not in df.columns:
            raise SystemExit(f"{ruta.name} no declara la columna {exigida}.")
    print(f"  {ruta.name}: {len(df)} establecimientos")
    return df


def _cargar_predicciones() -> pd.DataFrame | None:
    ruta = PROCESADO / "predicciones_factores.parquet"
    if not ruta.exists():
        return None
    pred = pd.read_parquet(ruta)
    pred.columns = [str(c).strip() for c in pred.columns]
    print(f"  predicciones_factores.parquet: {pred.shape[0]} filas, columnas {list(pred.columns)[:12]}")
    return pred


def _columna(df: pd.DataFrame, *candidatas: str) -> str | None:
    normal = {str(c).strip().upper(): str(c) for c in df.columns}
    for nombre in candidatas:
        if nombre.upper() in normal:
            return normal[nombre.upper()]
    return None


def evaluar(ciclo: str) -> int:
    print("=" * 62)
    print("Acierto en la seleccion: quien recibe el beneficio")
    print("=" * 62 + "\n")

    print("1. Cargando el resultado oficial")
    oficial = _leer_sned(ciclo)

    print("\n2. Cargando la estimacion del modelo")
    predicciones = _cargar_predicciones()
    if predicciones is None:
        raise SystemExit(
            "No se encontro data/processed/predicciones_factores.parquet.\n"
            "Es el archivo que produce el cuaderno de modelamiento con el indice estimado\n"
            "por establecimiento. Sin el no hay nada que comparar contra el resultado real."
        )

    col_rbd = _columna(predicciones, "rbd", "RBD")
    col_pred = _columna(
        predicciones,
        "pred_INDICER", "INDICER_predicho", "indice_predicho", "INDICER_pred",
        "prediccion", "INDICER",
    )

    if col_rbd is None:
        # El archivo de predicciones no lleva llave: sus filas estan alineadas por
        # POSICION con la tabla de entrenamiento. Se reconstruye la llave desde
        # ahi, y solo si los largos coinciden exactamente. Emparejar por posicion
        # dos tablas de distinto largo produciria un cruce silenciosamente falso.
        ruta_tabla = PROCESADO / "tabla_modelo_largo.parquet"
        if not ruta_tabla.exists():
            raise SystemExit("Las predicciones no traen RBD y no existe tabla_modelo_largo.parquet.")
        tabla = pd.read_parquet(ruta_tabla)
        if len(tabla) != len(predicciones):
            raise SystemExit(
                f"No se puede alinear por posicion: la tabla tiene {len(tabla)} filas y las "
                f"predicciones {len(predicciones)}."
            )
        llave_tabla = _columna(tabla, "rbd", "RBD")
        ciclo_tabla = _columna(tabla, "BIENIO_PREMIO", "BIENIO", "CICLO")
        if llave_tabla is None:
            raise SystemExit("tabla_modelo_largo.parquet no declara columna RBD.")
        predicciones = predicciones.reset_index(drop=True).copy()
        predicciones["rbd"] = tabla[llave_tabla].reset_index(drop=True)
        if ciclo_tabla is not None:
            predicciones["BIENIO_PREMIO"] = tabla[ciclo_tabla].reset_index(drop=True)
        col_rbd = "rbd"
        print("  Llave reconstruida por posicion desde tabla_modelo_largo.parquet (largos iguales)")

    if col_pred is None:
        raise SystemExit(
            "No se pudo identificar la columna de RBD o la del indice estimado.\n"
            f"Columnas disponibles: {list(predicciones.columns)}"
        )
    print(f"  Usando '{col_pred}' como indice estimado y '{col_rbd}' como llave")

    col_ciclo = _columna(predicciones, "BIENIO_PREMIO", "BIENIO", "CICLO")
    if col_ciclo is not None:
        etiqueta = ciclo.replace("_", "-")
        coincide = predicciones[col_ciclo].astype(str) == etiqueta
        if coincide.any():
            predicciones = predicciones[coincide]
            print(f"  Filtrado al ciclo {etiqueta}: {len(predicciones)} filas")
        else:
            valores = sorted(predicciones[col_ciclo].astype(str).unique())[:8]
            print(f"  AVISO: el ciclo {etiqueta} no aparece en '{col_ciclo}' ({valores}).")
            print("         Se conservan todas las filas y la comparacion es indicativa.")

    print("\n3. Cruzando")
    oficial["_llave"] = oficial["RBD"].astype(str).str.strip().str.lstrip("0")
    predicciones = predicciones.copy()
    predicciones["_llave"] = predicciones[col_rbd].astype(str).str.strip().str.lstrip("0")
    predicciones["_estimado"] = pd.to_numeric(predicciones[col_pred], errors="coerce")
    predicciones = predicciones.dropna(subset=["_estimado"]).drop_duplicates("_llave")

    datos = oficial.merge(predicciones[["_llave", "_estimado"]], on="_llave", how="inner")
    datos = datos[datos["CLUSTER"].notna() & datos["SEL"].notna()]
    print(f"  Establecimientos con resultado oficial y estimacion: {len(datos)}")
    if datos.empty:
        raise SystemExit("El cruce quedo vacio: revisa el formato de la llave RBD.")

    datos["_real"] = datos["SEL"].astype(str).str.strip().isin(SELECCIONADO)

    print("\n4. Reproduciendo la seleccion por Grupo Homogeneo")
    print("   Para cada grupo se toma el numero REAL de seleccionados y se pregunta")
    print("   si el modelo habria elegido a los mismos establecimientos.\n")

    elegidos: list[bool] = []
    for _, grupo in datos.groupby("CLUSTER"):
        cupos = int(grupo["_real"].sum())
        orden = grupo.sort_values("_estimado", ascending=False)
        marca = pd.Series(False, index=orden.index)
        if cupos:
            marca.iloc[:cupos] = True
        elegidos.append(marca)
    datos["_estimado_selecciona"] = pd.concat(elegidos).reindex(datos.index)

    vp = int((datos["_real"] & datos["_estimado_selecciona"]).sum())
    fp = int((~datos["_real"] & datos["_estimado_selecciona"]).sum())
    fn = int((datos["_real"] & ~datos["_estimado_selecciona"]).sum())
    vn = int((~datos["_real"] & ~datos["_estimado_selecciona"]).sum())

    precision = vp / (vp + fp) if vp + fp else 0.0
    recuerdo = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * recuerdo / (precision + recuerdo) if precision + recuerdo else 0.0
    exactitud = (vp + vn) / len(datos)

    print("  Matriz de confusion")
    print(f"    {'':<26}{'premiado real':>16}{'no premiado':>14}")
    print(f"    {'el modelo lo premia':<26}{vp:>16}{fp:>14}")
    print(f"    {'el modelo no lo premia':<26}{fn:>16}{vn:>14}")

    print("\n  Metricas")
    print(f"    Precision  {precision:.4f}   de los que el modelo premia, cuantos si lo eran")
    print(f"    Recuerdo   {recuerdo:.4f}   de los premiados reales, cuantos detecta")
    print(f"    F1         {f1:.4f}")
    print(f"    Exactitud  {exactitud:.4f}   sobre {len(datos)} establecimientos")

    base = datos["_real"].mean()
    print(f"\n  Tasa base de premiados: {base:.4f}")
    print(f"  Un clasificador que premiara al azar acertaria {base:.4f} de precision.")
    print(f"  El modelo obtiene {precision:.4f}: {precision / base:.2f} veces esa referencia.")

    print("\n  Los errores de frontera importan mas que los otros:")
    fallidos = datos[datos["_real"] & ~datos["_estimado_selecciona"]]
    if not fallidos.empty:
        print(f"    {len(fallidos)} establecimientos premiados que el modelo dejo fuera.")
        print("    Son el costo real de equivocarse: un sostenedor que planifico sin el beneficio.")

    print(
        "\n  Esta medicion NO habilita anticipar la subvencion: corre sobre un ciclo\n"
        "  cerrado y la seleccion depende de como se muevan los demas del grupo."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--ciclo", default="2024_2025", help="Ciclo a evaluar, formato 2024_2025")
    args = analizador.parse_args(argv)
    return evaluar(args.ciclo)


if __name__ == "__main__":
    sys.exit(main())
