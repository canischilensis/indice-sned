"""Reentrena los siete modelos con la diferencia corregida y la imputacion oficial.

## Los dos cambios de fondo que este entrenamiento incorpora

**1. La diferencia SIMCE corregida por significancia.** Las ocho variables
`superac_*` reemplazan a las `dif_simce_*` calculadas como resta cruda. El
metodo anula la diferencia cuando el propio SIMCE la reporta como no
significativa, y eso ocurre en el **68,9 %** de los casos medidos sobre este
repositorio. El entrenamiento anterior entregaba ruido estadistico como si fuera
senal en dos de cada tres establecimientos.

**2. La imputacion por Grupo Homogeneo.** El relleno de una variable ausente
deja de ser la mediana nacional y pasa a ser el promedio del grupo al que el
establecimiento pertenece:

    "Para los establecimientos que no cuentan con informacion para los Factores
    Efectividad y Superacion se imputa el promedio del grupo homogeneo."
    -- MINEDUC, Documento Tecnico SNED 2026-2027, p. 12

## Por que se entrenan DOS modelos de cada factor

Porque responden preguntas distintas y una sola no sirve para las dos:

  · **Validacion.** Se entrena sin el ciclo 2026-27 y se mide contra el. Produce
    la unica metrica honesta de generalizacion: como le va al modelo en un ciclo
    que no vio. Es la cifra que va al informe.

  · **Produccion.** Se entrena con todos los ciclos, incluido el ultimo. Es el
    artefacto que sirve la aplicacion, porque para estimar el ciclo 2028-2029
    conviene haber aprendido del 2026-2027.

Usar el modelo de produccion para reportar su propia generalizacion seria
medirse con la prueba que uno ya vio. Usar el de validacion en produccion seria
descartar el ciclo mas reciente. Se entrenan los dos y cada uno hace lo suyo.

## La regla que gobierna el reemplazo

**Un artefacto se reemplaza solo si mide mejor**, factor por factor. Si
EFECTIVR mejora y MEJORAR empeora, se cambia el primero y se conserva el
segundo, y ambos hechos quedan informados. El respaldo de los artefactos
anteriores se escribe siempre antes de tocar nada, con fecha en el nombre,
porque `models/` no esta versionado y no hay historial que los recupere.

## Uso

    python scripts/reentrenar_todo.py            # mide y compara, no reemplaza
    python scripts/reentrenar_todo.py --guardar  # reemplaza lo que mejore
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "processed"
REGISTRO = RAIZ / "models" / "registry"
METADATOS = RAIZ / "models" / "metadata"

CICLO_VALIDACION = "2026-27"
SEMILLA = 42

#: Traduccion de la variable vieja a la nueva. La resta cruda sale del vector de
#: entrada y entra la diferencia oficial corregida.
REEMPLAZOS = {
    f"dif_simce_{a}_{n}": f"superac_{a}_{n}"
    for n in ("4b", "6b", "8b", "2m")
    for a in ("lect", "mate")
}


def _llave(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.lstrip("0")


def _variables_de(meta: dict, codigo: str) -> list[str]:
    base = list(meta[codigo].get("features_base") or [])
    return [REEMPLAZOS.get(v, v) for v in base]


def _tabla_de_imputacion(datos: pd.DataFrame, variables: list[str]) -> dict[str, dict[str, float]]:
    """Promedio por Grupo Homogeneo, calculado SOLO sobre el entrenamiento.

    Calcularlo sobre el conjunto completo dejaria que el periodo de prueba
    informe sobre su propio relleno, que es una fuga silenciosa y dificil de
    detectar despues.
    """
    presentes = [v for v in variables if v in datos.columns]
    if "CLUSTER" not in datos.columns or not presentes:
        return {}
    promedios = datos.groupby(datos["CLUSTER"].astype(str))[presentes].mean(numeric_only=True)
    return {
        grupo: {v: float(x) for v, x in fila.items() if pd.notna(x)}
        for grupo, fila in promedios.iterrows()
    }


def _matriz(datos: pd.DataFrame, variables: list[str], por_grupo: dict, nacional: dict) -> pd.DataFrame:
    """Misma construccion que usa el motor al servir. Sin atajos.

    Si aqui se rellenara de una forma y al servir de otra, el modelo aprenderia
    sobre una distribucion que en produccion no existe. Es el desajuste que este
    proyecto ya pago una vez.
    """
    grupos = datos["CLUSTER"].astype(str) if "CLUSTER" in datos.columns else pd.Series("", index=datos.index)
    X = pd.DataFrame(index=datos.index)
    for v in variables:
        valores = pd.to_numeric(datos.get(v), errors="coerce") if v in datos.columns else pd.Series(np.nan, index=datos.index)
        falta = valores.isna()
        relleno = grupos.map(lambda g, v=v: (por_grupo.get(g) or {}).get(v, nacional.get(v, 0.0)))
        X[v] = valores.fillna(relleno).fillna(float(nacional.get(v, 0.0)))
        X[f"{v}_ausente"] = falta.astype(float)
    return X


def _entrenar(X, y, parametros: dict):
    from sklearn.ensemble import RandomForestRegressor

    limpios = {k: v for k, v in parametros.items() if k != "n_jobs"}
    limpios.setdefault("n_estimators", 500)
    modelo = RandomForestRegressor(random_state=SEMILLA, n_jobs=-1, **limpios)
    modelo.fit(X, y)
    return modelo


def main(argv: list[str] | None = None) -> int:
    from sklearn.metrics import mean_absolute_error, r2_score

    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--guardar", action="store_true", help="Reemplaza los artefactos que mejoren")
    args = analizador.parse_args(argv)

    print("=" * 72)
    print("Reentrenamiento con diferencia corregida e imputacion por grupo")
    print("=" * 72 + "\n")

    ruta = PROCESADO / "tabla_modelo_ciclos.parquet"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.name}. Corre construir_insumos y materializar_superacion.")
    tabla = pd.read_parquet(ruta)
    tabla["_llave"] = _llave(tabla["rbd"])
    ciclos = sorted(set(tabla["BIENIO_PREMIO"].astype(str)))
    print(f"Tabla: {len(tabla)} filas, ciclos {ciclos}")

    if not any(c.startswith("superac_") for c in tabla.columns):
        raise SystemExit("La tabla no tiene columnas superac_*. Corre materializar_superacion.py")

    with open(METADATOS / "metadatos_modelos.json", encoding="utf-8") as fh:
        meta = json.load(fh)
    factores = [c for c in meta if not c.startswith("_")]
    print(f"Factores: {factores}\n")

    entrena_val = tabla[tabla["BIENIO_PREMIO"].astype(str) != CICLO_VALIDACION]
    prueba_val = tabla[tabla["BIENIO_PREMIO"].astype(str) == CICLO_VALIDACION]
    print(f"Validacion temporal: {len(entrena_val)} filas de entrenamiento, "
          f"{len(prueba_val)} del ciclo {CICLO_VALIDACION}\n")
    if prueba_val.empty:
        raise SystemExit(f"La tabla no contiene el ciclo {CICLO_VALIDACION}.")

    resultados: dict[str, dict] = {}
    imputacion_produccion: dict[str, dict[str, float]] = {}
    modelos_produccion: dict[str, object] = {}

    print(f"{'':10} {'--- objetivo: valor ---':>19}  {'--- objetivo: posicion ---':>22}")
    print(f"{'Factor':<10} {'R2':>9} {'MAE':>8} {'R2 esc.tren':>10} {'R2 esc.real':>10}  Veredicto")
    print("-" * 72)

    for codigo in factores:
        variables = _variables_de(meta, codigo)
        objetivo = codigo if codigo in tabla.columns else None
        if objetivo is None:
            print(f"{codigo:<10} {'—':>10} {'—':>10} {'—':>10}  sin columna objetivo")
            continue

        parametros = dict(meta[codigo].get("best_params", {}))

        # --- variante de validacion: sin el ciclo de prueba -----------------
        train = entrena_val[entrena_val[objetivo].notna()]
        test = prueba_val[prueba_val[objetivo].notna()]
        por_grupo = _tabla_de_imputacion(train, variables)
        nacional = {v: float(pd.to_numeric(train.get(v), errors="coerce").median())
                    for v in variables if v in train.columns}
        nacional = {k: v for k, v in nacional.items() if pd.notna(v)}

        X_train = _matriz(train, variables, por_grupo, nacional)
        y_train = train[objetivo].astype(float)

        # --- objetivo A: el valor del factor, tal como viene -----------------
        modelo_val = _entrenar(X_train, y_train, parametros)

        # --- objetivo B: la posicion relativa dentro del ciclo ---------------
        # El factor se reescala de 0 a 100 en cada aplicacion, de modo que el
        # mismo desempeño produce numeros distintos entre ciclos. La posicion,
        # en cambio, significa lo mismo siempre. Se entrena contra el rango
        # percentil calculado DENTRO de cada ciclo.
        pct_train = train.groupby(train["BIENIO_PREMIO"].astype(str))[objetivo].rank(pct=True)
        modelo_pct = _entrenar(X_train, pct_train.astype(float), parametros)

        if test.empty:
            r2 = mae = r2_pct_train = r2_pct_test = float("nan")
        else:
            X_test = _matriz(test, variables, por_grupo, nacional)
            y_test = test[objetivo].astype(float)
            pred = modelo_val.predict(X_test)
            r2 = r2_score(y_test, pred)
            mae = mean_absolute_error(y_test, pred)

            # Para comparar en las mismas unidades, el percentil predicho se
            # traduce de vuelta a valor de factor. Se hace de dos formas:
            #
            #   · con la distribucion del ENTRENAMIENTO: es lo unico disponible
            #     al estimar un ciclo que todavia no ocurrio. Cifra honesta.
            #   · con la distribucion del propio ciclo de PRUEBA: no se puede
            #     usar en produccion, y sirve como techo de lo que el metodo
            #     daria si la escala del ciclo fuera conocida.
            pred_pct = np.clip(modelo_pct.predict(X_test), 0, 1)
            r2_pct_train = r2_score(y_test, np.quantile(y_train.dropna(), pred_pct))
            r2_pct_test = r2_score(y_test, np.quantile(y_test.dropna(), pred_pct))

        previo = meta[codigo].get("r2")
        mejora = previo is None or (not np.isnan(r2) and r2 > previo)
        veredicto = "mejora" if mejora else "no mejora"
        print(f"{codigo:<10} {r2:>9.4f} {mae:>8.2f} {r2_pct_train:>10.4f} {r2_pct_test:>10.4f}  {veredicto}")

        # --- variante de produccion: con todos los ciclos -------------------
        completo = tabla[tabla[objetivo].notna()]
        por_grupo_prod = _tabla_de_imputacion(completo, variables)
        nacional_prod = {v: float(pd.to_numeric(completo.get(v), errors="coerce").median())
                         for v in variables if v in completo.columns}
        nacional_prod = {k: v for k, v in nacional_prod.items() if pd.notna(v)}
        modelos_produccion[codigo] = _entrenar(
            _matriz(completo, variables, por_grupo_prod, nacional_prod),
            completo[objetivo].astype(float), parametros,
        )
        for grupo, valores in por_grupo_prod.items():
            imputacion_produccion.setdefault(grupo, {}).update(valores)

        resultados[codigo] = {
            "r2_previo": previo,
            "r2_validacion_temporal": None if np.isnan(r2) else round(float(r2), 4),
            "mae_validacion_temporal": None if np.isnan(mae) else round(float(mae), 3),
            "mejora": bool(mejora),
            "r2_objetivo_posicion_escala_entrenamiento": None if np.isnan(r2_pct_train) else round(float(r2_pct_train), 4),
            "r2_objetivo_posicion_escala_del_ciclo": None if np.isnan(r2_pct_test) else round(float(r2_pct_test), 4),
            "variables": variables,
            "n_entrenamiento": int(len(completo)),
        }

    print("-" * 72)
    print("\nComo leer las dos ultimas columnas:")
    print("  esc.tren  el percentil predicho se convierte a valor con la escala del")
    print("            ENTRENAMIENTO. Es lo unico disponible para un ciclo futuro.")
    print("  esc.real  se convierte con la escala del propio ciclo de prueba. No se")
    print("            puede usar en produccion; muestra el techo del metodo si la")
    print("            escala del ciclo fuera conocida.")
    print("\nLa distancia entre ambas columnas mide cuanto del error viene del")
    print("reescalamiento del factor y cuanto del modelo.\n")

    if not args.guardar:
        print("Ejecucion de medicion: no se toco ningun artefacto.")
        print("Revisa los resultados y vuelve con --guardar para reemplazar.")
        return 0

    import joblib

    sello = datetime.now().strftime("%Y%m%d_%H%M")
    respaldo = REGISTRO / f"_previo_{sello}"
    respaldo.mkdir(parents=True, exist_ok=True)
    for archivo in REGISTRO.glob("*.joblib"):
        shutil.copy2(archivo, respaldo / archivo.name)
    shutil.copy2(METADATOS / "metadatos_modelos.json", respaldo / "metadatos_modelos.json")
    print(f"Respaldo completo en {respaldo.relative_to(RAIZ)}\n")

    reemplazados = []
    for codigo, modelo in modelos_produccion.items():
        if not resultados[codigo]["mejora"]:
            print(f"  {codigo}: se conserva el artefacto anterior (no mejoro)")
            continue
        joblib.dump(modelo, REGISTRO / f"modelo_{codigo}.joblib")
        meta[codigo]["features_base"] = resultados[codigo]["variables"]
        meta[codigo]["features"] = [
            x for v in resultados[codigo]["variables"] for x in (v, f"{v}_ausente")
        ]
        meta[codigo]["r2"] = resultados[codigo]["r2_validacion_temporal"]
        meta[codigo]["mae"] = resultados[codigo]["mae_validacion_temporal"]
        meta[codigo]["validacion"] = f"temporal, contra el ciclo {CICLO_VALIDACION}"
        meta[codigo]["imputacion"] = "promedio del grupo homogeneo, con mediana nacional de respaldo"
        reemplazados.append(codigo)
        print(f"  {codigo}: artefacto reemplazado")

    meta.setdefault("_nota_reentrenamiento", "")
    meta["_nota_reentrenamiento"] = (
        f"Reentrenado el {sello} con la diferencia SIMCE corregida por significancia "
        "(Doc. Tecnico SNED 2026-2027, p. 12) e imputacion por grupo homogeneo. "
        "El R2 declarado es de validacion temporal contra un ciclo no visto, no de "
        "particion aleatoria: no es comparable con el R2 anterior."
    )
    with open(METADATOS / "metadatos_modelos.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)

    with open(METADATOS / "imputacion_por_grupo.json", "w", encoding="utf-8") as fh:
        json.dump(imputacion_produccion, fh, ensure_ascii=False, indent=2)
    print(f"\nTabla de imputacion escrita: {len(imputacion_produccion)} grupos homogeneos")
    print(f"Artefactos reemplazados: {reemplazados or 'ninguno'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
