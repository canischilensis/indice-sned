"""Reentrena el factor Superacion con la diferencia corregida por significancia.

## Por que existe

El cuaderno de entrenamiento calculo la variacion del SIMCE a mano, como
`puntaje_actual - puntaje_previo`. El metodo oficial no hace eso:

    "Las diferencias corregidas por significancia corresponden a las diferencias
    reportadas estandarizadas, en los casos en que estas sean significativas
    estadisticamente, y se consideran nulas en los casos en que el SIMCE reporta
    las diferencias como no significativas estadisticamente."
    -- MINEDUC, Documento Tecnico SNED 2026-2027, p. 12

La diferencia no es menor: en 4o basico Lectura 2018, **5.105 de 7.414
establecimientos tienen `sigdif = 0`**, es decir un 69 % de las diferencias no es
estadisticamente significativa y debe valer cero. El entrenamiento actual les
entrego ruido como si fuera senal, y el R2 del factor Superacion es 0,1999: el
peor de los seis.

Ademas, las bases publicadas traen dos variables de contexto que el modelo no
usa: `difgru_*` —brecha contra el promedio del grupo socioeconomico— y
`siggru_*` —si esa brecha es significativa—.

## Que hace, en orden

  1. Lee los Excel crudos del SIMCE y extrae, por RBD, las columnas oficiales
     `dif_*`, `sigdif_*`, `difgru_*`, `siggru_*` y `cod_grupo`.
  2. Construye la diferencia corregida segun la regla citada arriba.
  3. Entrena DOS modelos sobre la MISMA particion: uno con las variables
     actuales y otro con las corregidas mas el contexto de grupo.
  4. Informa los dos R2. **No reemplaza nada** salvo que se pase `--guardar`.

## Disciplina de la comparacion

Una variable en movimiento: el conjunto de variables de entrada. Mismo
algoritmo, mismos hiperparametros —los que ya estan en los metadatos—, misma
particion y misma semilla. Si el R2 sube, sube por el dato y no por la suerte.

La particion agrupa por RBD: ningun establecimiento puede estar a la vez en
entrenamiento y en prueba. Es el mismo control anti-fuga que verifica
`tests/unitarias/q2/test_contrato_del_indice.py`.

## Uso

    python scripts/reentrenar_superacion.py                 # mide, no toca nada
    python scripts/reentrenar_superacion.py --guardar       # reemplaza el artefacto

El respaldo del artefacto anterior se escribe siempre antes de reemplazar, con
la fecha en el nombre. Nada se pisa sin copia.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "raw" / "simce"
PROCESADO = RAIZ / "data" / "processed"
REGISTRO = RAIZ / "models" / "registry"
METADATOS = RAIZ / "models" / "metadata" / "metadatos_modelos.json"

#: Archivos que corresponden al bienio de premio 2018-19. La diferencia que
#: cada archivo reporta ya es contra la medicion anterior del mismo nivel: no
#: hay que restar nada a mano, que es justamente el error que se corrige.
ARCHIVOS_2018_19 = {
    "4b": "simce4b2018_rbd_publica_final.xlsx",
    "6b": "simce6b2018_rbd_publica_final.xlsx",
    "8b": "simce8b2019_rbd.xlsx",
    "2m": "simce2m2018_rbd_publica_final.xlsx",
}

ASIGNATURAS = ("lect", "mate")
SEMILLA = 42


# --- 1. extraccion desde el dato crudo --------------------------------------


def _columna(df: pd.DataFrame, patron: str) -> str | None:
    """Ubica una columna por patron, tolerando variaciones de nombre.

    Los archivos de la Agencia no son homogeneos entre anios: el sufijo `_rbd`
    aparece y desaparece, y el nivel se escribe pegado a la asignatura. Buscar
    por expresion regular evita una tabla de nombres que envejeceria mal.
    """
    regex = re.compile(patron, re.IGNORECASE)
    for columna in df.columns:
        if regex.fullmatch(str(columna).strip()):
            return str(columna)
    return None


def extraer_nivel(nivel: str, archivo: Path) -> pd.DataFrame | None:
    if not archivo.exists():
        print(f"  AVISO: no existe {archivo.name}; el nivel {nivel} queda fuera.")
        return None

    crudo = pd.read_excel(archivo, dtype={"rbd": str, "RBD": str})
    rbd = _columna(crudo, r"rbd")
    if rbd is None:
        print(f"  AVISO: {archivo.name} no declara columna RBD; se omite.")
        return None

    salida = pd.DataFrame({"rbd": crudo[rbd].astype(str).str.strip()})
    encontradas = 0

    for asignatura in ASIGNATURAS:
        col_dif = _columna(crudo, rf"dif_{asignatura}{nivel}(_rbd)?")
        col_sig = _columna(crudo, rf"sigdif_{asignatura}{nivel}(_rbd)?")
        col_gru = _columna(crudo, rf"difgru_{asignatura}{nivel}(_rbd)?")
        col_sgru = _columna(crudo, rf"siggru_{asignatura}{nivel}(_rbd)?")

        if col_dif is not None and col_sig is not None:
            dif = pd.to_numeric(crudo[col_dif], errors="coerce")
            sig = pd.to_numeric(crudo[col_sig], errors="coerce")
            # La regla oficial, literal: vale la diferencia solo si el propio
            # SIMCE la reporto como significativa; si no, vale cero.
            salida[f"superac_{asignatura}_{nivel}"] = np.where(
                sig.fillna(0) != 0, dif, 0.0
            )
            salida[f"superac_sig_{asignatura}_{nivel}"] = sig.fillna(0)
            encontradas += 1

        if col_gru is not None:
            salida[f"brecha_{asignatura}_{nivel}"] = pd.to_numeric(
                crudo[col_gru], errors="coerce"
            )
            encontradas += 1
        if col_sgru is not None:
            salida[f"brecha_sig_{asignatura}_{nivel}"] = pd.to_numeric(
                crudo[col_sgru], errors="coerce"
            ).fillna(0)

    grupo = _columna(crudo, r"cod_grupo")
    if grupo is not None:
        salida["cod_grupo"] = pd.to_numeric(crudo[grupo], errors="coerce")

    if encontradas == 0:
        print(f"  AVISO: {archivo.name} no trae columnas oficiales de diferencia.")
        return None

    print(f"  {archivo.name}: {len(salida)} filas, {salida.shape[1] - 1} columnas utiles.")
    return salida


def construir_insumo() -> pd.DataFrame:
    print("1. Extrayendo las columnas oficiales desde el dato crudo")
    partes = [
        p for nivel, nombre in ARCHIVOS_2018_19.items()
        if (p := extraer_nivel(nivel, CRUDO / nombre)) is not None
    ]
    if not partes:
        raise SystemExit(
            "No se pudo extraer ninguna columna oficial. Revisa que los Excel esten "
            f"en {CRUDO} con los nombres declarados en ARCHIVOS_2018_19."
        )

    insumo = partes[0]
    for parte in partes[1:]:
        insumo = insumo.merge(parte, on="rbd", how="outer", suffixes=("", "_dup"))
    insumo = insumo.loc[:, ~insumo.columns.str.endswith("_dup")]

    columnas_superac = [c for c in insumo.columns if c.startswith("superac_") and "_sig_" not in c]
    if columnas_superac:
        nulas = (insumo[columnas_superac] == 0).sum().sum()
        totales = insumo[columnas_superac].notna().sum().sum()
        print(
            f"\n  Diferencias anuladas por no ser significativas: {nulas} de {totales} "
            f"({nulas / max(totales, 1):.1%}). Es la correccion que el metodo oficial exige."
        )

    destino = PROCESADO / "simce_superacion_corregida.parquet"
    insumo.to_parquet(destino, index=False)
    print(f"  Insumo escrito en {destino.relative_to(RAIZ)}")
    return insumo


# --- 2. comparacion de modelos ----------------------------------------------


def _tabla_objetivo() -> pd.DataFrame:
    for nombre in ("tabla_modelo_largo.parquet", "tabla_entrenamiento_modelo.parquet"):
        ruta = PROCESADO / nombre
        if ruta.exists():
            tabla = pd.read_parquet(ruta)
            print(f"  Tabla de entrenamiento: {nombre} ({tabla.shape[0]} filas)")
            return tabla
    raise SystemExit(f"No se encontro la tabla de entrenamiento en {PROCESADO}")


def _normalizar_rbd(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.lstrip("0")


def comparar(insumo: pd.DataFrame, guardar: bool) -> None:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import GroupShuffleSplit

    print("\n2. Preparando la comparacion")
    tabla = _tabla_objetivo()

    objetivo = next((c for c in ("SUPERAR", "SUPERACR", "superar") if c in tabla.columns), None)
    if objetivo is None:
        raise SystemExit(f"La tabla no declara el factor Superacion. Columnas: {list(tabla.columns)[:30]}")

    llave = next((c for c in ("rbd", "RBD") if c in tabla.columns), None)
    if llave is None:
        raise SystemExit("La tabla de entrenamiento no declara columna RBD.")

    columna_bienio = next(
        (c for c in tabla.columns if "BIENIO" in str(c).upper() or "CICLO" in str(c).upper()),
        None,
    )
    if columna_bienio is not None:
        valores = sorted(str(v) for v in tabla[columna_bienio].dropna().unique())
        print(f"  Columna de ciclo: '{columna_bienio}' -> {valores[:10]}")
        objetivo_ciclo = [v for v in valores if "2018" in v or "2019" in v]
        if objetivo_ciclo:
            antes = len(tabla)
            tabla = tabla[tabla[columna_bienio].astype(str).isin(objetivo_ciclo)]
            print(f"  Filtrado a {objetivo_ciclo}: {antes} -> {len(tabla)} filas")
        else:
            # No se filtra a ciegas: sin ciclo coincidente se conserva todo y se
            # declara. Un filtro que deja cero filas es peor que no filtrar.
            print("  AVISO: ningun ciclo menciona 2018 o 2019. Se conservan todas las filas.")

    tabla = tabla.copy()
    tabla["_llave"] = _normalizar_rbd(tabla[llave])
    insumo = insumo.copy()
    insumo["_llave"] = _normalizar_rbd(insumo["rbd"])

    comunes = set(tabla["_llave"]) & set(insumo["_llave"])
    print(
        f"  Cruce por RBD: {len(set(tabla['_llave']))} en la tabla, "
        f"{len(set(insumo['_llave']))} en el insumo, {len(comunes)} en comun"
    )
    if not comunes:
        print(f"    ejemplo tabla : {list(tabla['_llave'])[:5]}")
        print(f"    ejemplo insumo: {list(insumo['_llave'])[:5]}")
        raise SystemExit("Las llaves no cruzan. Compara los ejemplos de arriba.")

    datos = tabla.merge(insumo.drop(columns=["rbd"]), on="_llave", how="left")
    datos = datos[datos[objetivo].notna()]
    print(f"  Filas con factor conocido: {len(datos)}")

    actuales = [c for c in datos.columns if c.startswith("dif_simce_") or re.fullmatch(r"simce_(lect|mate)_\w+", str(c))]
    nuevas = [
        c for c in datos.columns
        if c.startswith(("superac_", "brecha_")) or c == "cod_grupo"
    ]
    nuevas = [c for c in nuevas if datos[c].notna().sum() > 0]
    base_comun = [c for c in actuales if not c.startswith("dif_simce_")]

    if not nuevas:
        raise SystemExit("El cruce no aporto ninguna columna nueva: revisa la llave RBD.")

    print(f"  Variables actuales: {len(actuales)} | nuevas: {len(nuevas)}")

    # Tres escenarios y no dos, porque con dos no se puede saber si el salto lo
    # produjo la correccion oficial o simplemente haber agregado 33 variables.
    # El segundo mueve UNA cosa: la misma cantidad de senal, corregida.
    solo_corregidas = base_comun + [
        c for c in nuevas if c.startswith("superac_") and "_sig_" not in c
    ]
    escenarios = {
        "1 · resta cruda (actual)": actuales,
        "2 · solo diferencia corregida": solo_corregidas,
        "3 · corregida + contexto de grupo": base_comun + nuevas,
    }

    particion = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEMILLA)
    entrena, prueba = next(particion.split(datos, groups=datos["_llave"]))
    solapados = set(datos.iloc[entrena]["_llave"]) & set(datos.iloc[prueba]["_llave"])
    if solapados:
        raise SystemExit(f"Fuga: {len(solapados)} establecimientos en ambas particiones.")
    print(f"  Particion por RBD: {len(entrena)} entrenamiento / {len(prueba)} prueba, 0 solapados")

    with open(METADATOS, encoding="utf-8") as fuente:
        meta = json.load(fuente)
    parametros = dict(meta.get("SUPERAR", {}).get("best_params", {}))
    parametros.setdefault("n_estimators", 500)
    print(f"  Hiperparametros (los ya registrados): {parametros}")

    print("\n3. Resultados\n")
    print(f"  {'Escenario':<32} {'R2':>8} {'MAE':>8} {'Vars':>6}")
    print("  " + "-" * 56)

    resultados = {}
    for etiqueta, columnas in escenarios.items():
        X = datos[columnas].apply(pd.to_numeric, errors="coerce")
        X = X.fillna(X.median(numeric_only=True))
        y = datos[objetivo].astype(float)

        modelo = RandomForestRegressor(random_state=SEMILLA, n_jobs=-1, **parametros)
        modelo.fit(X.iloc[entrena], y.iloc[entrena])
        prediccion = modelo.predict(X.iloc[prueba])
        r2 = r2_score(y.iloc[prueba], prediccion)
        mae = mean_absolute_error(y.iloc[prueba], prediccion)
        resultados[etiqueta] = (r2, mae, modelo, columnas)
        print(f"  {etiqueta:<32} {r2:>8.4f} {mae:>8.3f} {len(columnas):>6}")

    r2_actual = resultados["1 · resta cruda (actual)"][0]
    r2_corregida = resultados["2 · solo diferencia corregida"][0]
    r2_nuevo = resultados["3 · corregida + contexto de grupo"][0]
    delta = r2_nuevo - r2_actual

    print("\n  Descomposicion del efecto:")
    print(f"    por corregir la diferencia : {r2_corregida - r2_actual:+.4f}")
    print(f"    por el contexto de grupo   : {r2_nuevo - r2_corregida:+.4f}")
    print(f"    total                      : {delta:+.4f}")
    print(
        "\n  El R2 de 0,1999 que figura en los metadatos NO es comparable con estas"
        "\n  cifras: se midio con otra tabla, otra particion y 16 variables. La"
        "\n  comparacion valida es la de esta tabla, entre los tres escenarios."
    )

    if delta <= 0:
        print(
            "\n  El dato NO respalda el cambio. Se informa asi y no se reemplaza nada:\n"
            "  la correccion es la correcta metodologicamente, pero sobre este objetivo\n"
            "  no mejora la estimacion. Ambas cosas pueden ser ciertas a la vez."
        )
    else:
        print("\n  El dato respalda el cambio.")

    if not guardar:
        print("\n  Ejecucion de medicion: no se toco ningun artefacto. Usa --guardar para reemplazar.")
        return

    if delta <= 0:
        print("\n  --guardar ignorado: no se reemplaza un artefacto por otro que mide peor.")
        return

    REGISTRO.mkdir(parents=True, exist_ok=True)
    destino = REGISTRO / "modelo_SUPERAR.joblib"
    if destino.exists():
        sello = datetime.now().strftime("%Y%m%d_%H%M")
        respaldo = REGISTRO / f"modelo_SUPERAR.previo_{sello}.joblib"
        shutil.copy2(destino, respaldo)
        print(f"\n  Respaldo del artefacto anterior: {respaldo.name}")

    import joblib

    _, _, modelo, columnas = resultados["3 · corregida + contexto de grupo"]
    joblib.dump(modelo, destino)
    print(f"  Artefacto reemplazado: {destino.name}")
    print(
        "\n  PENDIENTE MANUAL: actualizar 'features' y 'features_base' de SUPERAR en\n"
        f"  {METADATOS.relative_to(RAIZ)} con estas columnas:\n  {columnas}"
    )


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument(
        "--guardar", action="store_true",
        help="Reemplaza el artefacto SUPERAR si y solo si el R2 mejora. Respalda antes.",
    )
    args = analizador.parse_args(argv)

    print("=" * 62)
    print("Factor Superacion: diferencia corregida por significancia")
    print("MINEDUC, Documento Tecnico SNED 2026-2027, p. 12")
    print("=" * 62 + "\n")

    insumo = construir_insumo()
    comparar(insumo, args.guardar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
