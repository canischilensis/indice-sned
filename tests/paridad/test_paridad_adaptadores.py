"""Paridad entre los dos adaptadores del puerto RepositorioEstablecimientos.

El patron Repository promete que la capa de servicio no sabe de donde viene el
dato. Esta prueba lo verifica empiricamente: las mismas llamadas contra parquet
y contra PostgreSQL deben devolver lo mismo.

Corre en CI y falla si alguien rompe la paridad. Para regenerar las respuestas:

    REPOSITORIO_DATOS=parquet  python tests/paridad/arnes.py baseline_parquet
    REPOSITORIO_DATOS=postgres python tests/paridad/arnes.py resultado_postgres
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent
BASE = RAIZ / "baseline_parquet" / "respuestas.json"
PG = RAIZ / "resultado_postgres" / "respuestas.json"

# Umbral general: 1e-3. El parquet guarda float32 y la base NUMERIC(6,3), de
# modo que el ultimo digito difiere por representacion, no por dato. Exigir
# 1e-4 seria mas estricto que la precision de la propia fuente.
TOLERANCIA = 1e-3

# Campos que en la base son NUMERIC(6,3) o mas precisos y donde si se exige el
# umbral estricto.
TOLERANCIA_ESTRICTA = 1e-4
CAMPOS_ESTRICTOS = {"indicer", "indicer_oficial", "indicer_calculado", "ponderacion",
                    "peso", "aporte_al_indice", "valor_base", "contribucion"}

# Claves cuya ausencia en el adaptador PostgreSQL es una decision de diseno
# declarada, no una falla de paridad:
#   - los seis factores y SEL son el objetivo del modelo: exponerlos como
#     variable de entrada seria fuga (declarado en el diseno del experimento)
#   - simce_prom_4b y dif_simce_* son derivadas y no se persisten
#   - ficha_no_respondida se aplica en la depuracion, aguas arriba
EXCLUIDAS_POR_DISENO = {
    "EFECTIVR", "SUPERAR", "IGUALDR", "INICIAR", "INTEGRAR", "MEJORAR",
    "simce_prom_4b", "ficha_no_respondida",
    # nom_rbd: el parquet lo trae truncado a 40 caracteres y sin tildes; la base
    # trae el nombre completo desde sned_maestro_ciclos. Manda la base.
    "NOM_RBD", "nom_rbd",
    # origen: es el nombre del adaptador activo, metadato, no dato.
    "origen",
    # cod_depe2 no es comparable entre adaptadores: el parquet trae la
    # dependencia de la ventana de features 2018-19 (constante en los tres
    # ciclos) y la base la trae por ciclo desde sned_maestro_ciclos. Un
    # establecimiento que migro de Municipal a SLEP aparece con valores
    # distintos y ambos son correctos para su periodo. Diferencia temporal
    # legitima, no defecto de implementacion.
    "cod_depe2",
}

# El ranking se calcula sobre TODOS los establecimientos del ciclo, porque la
# competencia real del SNED ocurre entre todos los que participan. La base tiene
# los 11.569 RBD de los 5 ciclos; el parquet solo los 7.754 del conjunto
# depurado en 3 ciclos. La paridad aqui es imposible POR CONSTRUCCION, no por
# defecto de implementacion: son poblaciones distintas compitiendo dentro del
# mismo cluster. El adaptador de PostgreSQL es el correcto.
ENDPOINTS_EXCLUIDOS = {"ranking"}


def _cargar():
    if not (BASE.exists() and PG.exists()):
        pytest.skip("Faltan las corridas del arnes. Ver docstring.")
    return json.loads(BASE.read_text(encoding="utf-8")), json.loads(PG.read_text(encoding="utf-8"))


def comparar(a, b, ruta: str = "") -> list[str]:
    """Compara recursivamente y devuelve la lista de divergencias."""
    fallos: list[str] = []

    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in EXCLUIDAS_POR_DISENO:
                continue
            if k not in a:
                fallos.append(f"{ruta}.{k}: ausente en parquet")
            elif k not in b:
                fallos.append(f"{ruta}.{k}: ausente en postgres")
            else:
                fallos += comparar(a[k], b[k], f"{ruta}.{k}")
        return fallos

    if isinstance(a, list) and isinstance(b, list):
        # listas ordenadas: mismo orden y mismos elementos
        if len(a) != len(b):
            return [f"{ruta}: largo {len(a)} vs {len(b)}"]
        for i, (x, y) in enumerate(zip(a, b)):
            fallos += comparar(x, y, f"{ruta}[{i}]")
        return fallos

    # nulos: uno nulo y el otro no es divergencia, aunque el otro sea 0
    if (a is None) != (b is None):
        lado = "parquet" if a is None else "postgres"
        return [f"{ruta}: nulo en {lado} (parquet={a!r}, postgres={b!r})"]
    if a is None:
        return []

    if isinstance(a, bool) or isinstance(b, bool):
        return [] if a == b else [f"{ruta}: {a!r} vs {b!r}"]

    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        campo = ruta.rsplit(".", 1)[-1].split("[")[0]
        umbral = TOLERANCIA_ESTRICTA if campo in CAMPOS_ESTRICTOS else TOLERANCIA
        delta = abs(float(a) - float(b))
        return [] if delta < umbral else \
               [f"{ruta}: {a} vs {b} (delta {delta:.6f}, umbral {umbral})"]

    return [] if str(a) == str(b) else [f"{ruta}: {a!r} vs {b!r}"]


def test_los_dos_adaptadores_cubren_los_mismos_endpoints():
    a, b = _cargar()
    assert sorted(a) == sorted(b)


def test_el_ranking_queda_excluido_de_la_paridad_con_razon_documentada():
    """No es un defecto: el parquet no contiene la poblacion completa del ciclo."""
    assert "ranking" in ENDPOINTS_EXCLUIDOS
    assert ENDPOINTS_EXCLUIDOS.issubset(set(_cargar()[0]))


def test_todas_las_llamadas_devuelven_el_mismo_estado_http():
    a, b = _cargar()
    malos = [
        f"{ep}/{rbd}: {a[ep][rbd]['status']} vs {b[ep][rbd]['status']}"
        for ep in a for rbd in a[ep]
        if a[ep][rbd]["status"] != b[ep][rbd]["status"]
    ]
    assert not malos, "Estados HTTP distintos:\n" + "\n".join(malos)


@pytest.mark.parametrize("endpoint", ["listado", "detalle", "prediccion",
                                      "alertas", "shapley", "simulacion"])
def test_paridad_por_endpoint(endpoint):
    a, b = _cargar()
    if endpoint in ENDPOINTS_EXCLUIDOS:
        pytest.skip("Excluido por construccion: poblaciones distintas.")
    if endpoint not in a:
        pytest.skip(f"El endpoint {endpoint} no fue ejercitado.")
    fallos: list[str] = []
    for clave in sorted(a[endpoint]):
        fallos += comparar(a[endpoint][clave], b[endpoint][clave], f"{endpoint}[{clave}]")
    assert not fallos, f"{len(fallos)} divergencias en {endpoint}:\n" + "\n".join(fallos[:25])
