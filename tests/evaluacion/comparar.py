"""Comparacion medida entre los dos adaptadores del puerto `AsesorDeGestion`.

Un bucle de ejecucion escrito a mano contra el agente ReAct que LangGraph trae de
fabrica, sobre los **mismos veinte casos criticos, sin modificar ninguno**. Que
esos casos sirvan para los dos sin tocarse no es una comodidad del arnes: es la
prueba de que el puerto era un puerto y no una promesa.

## Disciplina experimental

**Una variable en movimiento.** Aqui se mueve el orquestador y nada mas: mismo
doble del servicio, mismo catalogo de herramientas, mismo proveedor determinista
con los mismos disparadores, misma politica de salida. La comparacion entre
proveedores es otro experimento, con su propia tabla, y mezclarlas produciria
ocho celdas que se leen como fuerza bruta en vez de como diseno.

**El proveedor es el determinista, a proposito.** Sin red y sin clave, de modo
que la diferencia observada no puede venir de dos respuestas distintas del mismo
modelo. Lo que se mide es la orquestacion, no la suerte.

## Lo que la tabla no dice

No dice cual es mejor. Dice que cuesta cada uno para hacer lo mismo, y a partir
de ahi la eleccion depende de que necesite el sistema. Un framework que no se
usa por debajo de cierta complejidad no es un mal framework: es una herramienta
aplicada fuera de su rango.

    python tests/evaluacion/comparar.py
    python tests/evaluacion/comparar.py --json comparacion.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from arnes import BUCLE_SIMPLE, LANGGRAPH, ResultadoCaso, ejecutar  # noqa: E402

#: Paquetes que cada orquestador incorpora al entorno, por encima de lo que el
#: cuanto 5 ya necesitaba. Es la fila que mas informa en una decision de
#: arquitectura y la que ninguna comparacion de calidad muestra: se cuenta a
#: mano porque depende de la instalacion y no del codigo.
DEPENDENCIAS = {
    BUCLE_SIMPLE: (
        "httpx",
    ),
    LANGGRAPH: (
        "langgraph", "langgraph-checkpoint", "langgraph-prebuilt", "langgraph-sdk",
        "langchain-core", "langchain-protocol", "langsmith", "jsonpatch", "orjson",
        "ormsgpack", "requests-toolbelt", "uuid-utils", "websockets", "xxhash",
        "zstandard",
    ),
}


@dataclass
class Medicion:
    """Lo que se observa de un orquestador sobre los veinte casos."""

    orquestador: str
    casos: int
    aprobados: int
    ruteo_correcto: int
    cifras_fundadas: int
    sin_promesas: int
    rechazos_correctos: int
    resiliencia_correcta: int
    pasos_totales: int
    llamadas_al_modelo: int
    tokens_entrada: int
    tokens_salida: int
    costo_usd: float
    latencia_p50: int
    latencia_p95: int
    dependencias: int
    fallos: list[str] = field(default_factory=list)


def _percentil(valores: list[int], p: float) -> int:
    if not valores:
        return 0
    ordenados = sorted(valores)
    indice = max(0, min(len(ordenados) - 1, int(round(p * len(ordenados))) - 1))
    return ordenados[indice]


def medir(orquestador: str) -> tuple[Medicion, list[ResultadoCaso]]:
    resultados = ejecutar(orquestador)
    latencias = [r.milisegundos for r in resultados]
    medicion = Medicion(
        orquestador=orquestador,
        casos=len(resultados),
        aprobados=sum(1 for r in resultados if r.aprobado),
        ruteo_correcto=sum(1 for r in resultados if r.ruteo_correcto),
        cifras_fundadas=sum(1 for r in resultados if not r.cifras_sin_respaldo),
        sin_promesas=sum(1 for r in resultados if not r.promesas_detectadas),
        rechazos_correctos=sum(
            1 for r in resultados if r.categoria in ("Seguridad", "Alcance") and r.aprobado
        ),
        resiliencia_correcta=sum(
            1 for r in resultados if r.categoria == "Resiliencia" and r.aprobado
        ),
        pasos_totales=sum(r.pasos for r in resultados),
        llamadas_al_modelo=sum(r.llamadas_al_modelo for r in resultados),
        tokens_entrada=sum(r.tokens_entrada for r in resultados),
        tokens_salida=sum(r.tokens_salida for r in resultados),
        costo_usd=round(sum(r.costo_usd for r in resultados), 6),
        latencia_p50=_percentil(latencias, 0.50),
        latencia_p95=_percentil(latencias, 0.95),
        dependencias=len(DEPENDENCIAS[orquestador]),
        fallos=[f"{r.id}: {' | '.join(r.fallos)}" for r in resultados if not r.aprobado],
    )
    return medicion, resultados


_FILAS: tuple[tuple[str, str, str], ...] = (
    ("Casos aprobados", "aprobados", "/casos"),
    ("Ruteo correcto", "ruteo_correcto", "/casos"),
    ("Cifras fundadas (G-02)", "cifras_fundadas", "/casos"),
    ("Sin promesas (G-03)", "sin_promesas", "/casos"),
    ("Rechazos de politica", "rechazos_correctos", ""),
    ("Resiliencia 403/404/422/503", "resiliencia_correcta", ""),
    ("Llamadas a herramienta", "pasos_totales", ""),
    ("Llamadas al modelo", "llamadas_al_modelo", ""),
    ("Tokens de entrada", "tokens_entrada", ""),
    ("Tokens de salida", "tokens_salida", ""),
    ("Costo USD", "costo_usd", ""),
    ("Latencia p50 (ms)", "latencia_p50", ""),
    ("Latencia p95 (ms)", "latencia_p95", ""),
    ("Dependencias transitivas", "dependencias", ""),
)


def informe(a: Medicion, b: Medicion) -> str:
    ancho = 30
    lineas = [
        "COMPARACION DE ORQUESTADORES · 20 casos criticos, sin modificar",
        "=" * 74,
        "  Una variable en movimiento: el orquestador. Mismo doble del servicio,",
        "  mismo catalogo, mismo proveedor determinista, misma politica de salida.",
        "=" * 74,
        f"{'Metrica':<{ancho}} {a.orquestador:>19} {b.orquestador:>19}",
        "-" * 74,
    ]
    for rotulo, campo, sufijo in _FILAS:
        va, vb = getattr(a, campo), getattr(b, campo)
        cola = f"/{a.casos}" if sufijo == "/casos" else ""
        lineas.append(f"{rotulo:<{ancho}} {str(va) + cola:>19} {str(vb) + cola:>19}")
    lineas.append("=" * 74)

    for medicion in (a, b):
        if medicion.fallos:
            lineas.append(f"\nFallos de {medicion.orquestador}:")
            lineas.extend(f"  {f}" for f in medicion.fallos)

    lineas.append("")
    lineas.append(
        "El costo es cero porque el proveedor es el determinista: sin red y sin\n"
        "clave, para que la diferencia observada no pueda venir de dos respuestas\n"
        "distintas del mismo modelo. La medicion con un proveedor real es otro\n"
        "experimento, con su propia tabla."
    )
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description="Compara los dos orquestadores")
    analizador.add_argument("--json", default=None, help="Ruta donde escribir el detalle")
    args = analizador.parse_args(argv)

    propio, casos_propio = medir(BUCLE_SIMPLE)
    grafo, casos_grafo = medir(LANGGRAPH)
    print(informe(propio, grafo))

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {
                    "resumen": {m.orquestador: asdict(m) for m in (propio, grafo)},
                    "detalle": {
                        propio.orquestador: [asdict(r) for r in casos_propio],
                        grafo.orquestador: [asdict(r) for r in casos_grafo],
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nDetalle escrito en {args.json}")

    # La comparacion no falla porque un orquestador rinda menos: falla si alguno
    # deja de cumplir los casos. Medir no es aprobar.
    return 0 if not (propio.fallos or grafo.fallos) else 1


if __name__ == "__main__":
    raise SystemExit(main())
