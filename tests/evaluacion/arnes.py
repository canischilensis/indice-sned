"""Arnes de evaluacion del agente asesor.

Ejecuta los veinte casos criticos contra un doble del servicio y mide cinco
cosas, todas verificables y ninguna opinable:

  1. Ruteo de herramienta: eligio la herramienta que el caso declara.
  2. Fundamentacion de cifras: no cito ninguna magnitud que el servicio no
     devolviera. Es G-02 medido, no declarado.
  3. Ausencia de promesas de retorno: G-03.
  4. Resiliencia: ante 403, 404, 422 y 503 responde sin inventar cifras.
  5. Latencia del bucle contra un doble del servicio.

     Lo que este numero acota es el sobrecosto propio del agente: el bucle, los
     guardarrailes y la redaccion. No acota lo que espera un usuario. El doble
     responde en unidades de milisegundos porque devuelve cargas fijas; el
     servicio real calcula. Medicion puntual del 2026-08-10, misma consulta de
     explicacion por factor: 31 ms contra el doble, 5.906 ms contra el servicio
     levantado sobre parquet.

     Presentar el primero como latencia del sistema seria informar de menos por
     construccion del banco de pruebas.

    python tests/evaluacion/arnes.py              # informe por consola
    python tests/evaluacion/arnes.py --respuestas # ademas, que contesto el agente
    python tests/evaluacion/arnes.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Fuera de pytest nadie pone `quanta/` en la ruta: pytest lo hace por el
# `pythonpath` de pyproject.toml, y uvicorn por `--app-dir quanta`. Este arnes
# es un punto de entrada independiente, asi que resuelve la ruta el mismo.
_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parents[1]
for _ruta in (_AQUI, _RAIZ / "quanta"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from casos import CASOS, CasoCritico  # noqa: E402
from dobles import ServicioFalso  # noqa: E402
from q5_agente.bucle import AgenteDeBucleSimple  # noqa: E402
from q5_agente.contrato import Consulta  # noqa: E402
from q5_agente.guardarrailes import (  # noqa: E402
    Fundamentacion,
    PoliticaDeSalida,
    SanitizadorDeParametros,
)
from q5_agente.herramientas.catalogo import construir_catalogo  # noqa: E402
from q5_agente.proveedores.determinista import AdaptadorDeterminista  # noqa: E402


def _plano(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


@dataclass
class ResultadoCaso:
    id: str
    categoria: str
    descripcion: str
    aprobado: bool
    herramienta_usada: str | None
    ruteo_correcto: bool
    cifras_sin_respaldo: list[float]
    promesas_detectadas: list[str]
    milisegundos: int
    rechazada: bool
    motivo: str | None
    fallos: list[str]
    consulta: str = ""
    respuesta: str = ""
    llamada_exitosa: bool = False
    detalle_llamada: str = ""
    guardarrailes: list[str] = field(default_factory=list)


def construir_agente(servicio: ServicioFalso) -> AgenteDeBucleSimple:
    herramientas = construir_catalogo(servicio, SanitizadorDeParametros())
    proveedor = AdaptadorDeterminista({h.nombre: h.disparadores for h in herramientas.values()})
    return AgenteDeBucleSimple(proveedor, herramientas, PoliticaDeSalida(), max_pasos=3)


def evaluar_caso(
    caso: CasoCritico, agente: AgenteDeBucleSimple, servicio: ServicioFalso
) -> ResultadoCaso:
    inicio = time.monotonic()
    respuesta = agente.asesorar(
        Consulta(texto=caso.consulta, rbd=caso.rbd, usuario="evaluacion")
    )
    transcurrido = int((time.monotonic() - inicio) * 1000)

    politica = PoliticaDeSalida()
    # Mismo conjunto que uso el agente: cifras de dato mas cifras de mensajes
    # del sistema. Medir con un conjunto mas estrecho produciria falsos
    # positivos sobre los mensajes de error, que son datos y no invenciones.
    candidato = Fundamentacion(
        respuesta.texto,
        set(respuesta.cifras_citadas) | set(respuesta.cifras_de_diagnostico),
    )
    huerfanas = politica.cifras.cifras_sin_respaldo(candidato)
    promesas = politica.promesas.frases_detectadas(candidato)

    herramienta_usada = respuesta.llamadas[0].herramienta if respuesta.llamadas else None
    ruteo_correcto = herramienta_usada == caso.herramienta_esperada

    fallos: list[str] = []
    if not ruteo_correcto:
        fallos.append(
            f"ruteo: esperaba {caso.herramienta_esperada or 'ninguna herramienta'}, "
            f"uso {herramienta_usada or 'ninguna'}"
        )
    if huerfanas:
        fallos.append(f"G-02: cifras sin respaldo {[round(c, 2) for c in huerfanas]}")
    if promesas:
        fallos.append(f"G-03: promesas detectadas {promesas}")

    if caso.espera_fallo_de_herramienta:
        fallo_real = bool(respuesta.llamadas) and not respuesta.llamadas[0].exito
        if not fallo_real:
            fallos.append("resiliencia: se esperaba un fallo controlado de la herramienta")
    if caso.espera_rechazo and not respuesta.rechazada:
        fallos.append("politica: se esperaba que la respuesta fuera rechazada")

    plano = _plano(respuesta.texto)
    for frase in caso.frases_requeridas:
        if _plano(frase) not in plano:
            fallos.append(f"contenido: falta la frase requerida '{frase}'")
    for frase in caso.frases_prohibidas:
        if _plano(frase) in plano:
            fallos.append(f"contenido: aparece la frase prohibida '{frase}'")
    if caso.max_milisegundos is not None and transcurrido > caso.max_milisegundos:
        fallos.append(
            f"latencia: {transcurrido} ms supera el presupuesto de {caso.max_milisegundos}"
        )

    return ResultadoCaso(
        id=caso.id,
        categoria=caso.categoria,
        descripcion=caso.descripcion,
        aprobado=not fallos,
        herramienta_usada=herramienta_usada,
        ruteo_correcto=ruteo_correcto,
        cifras_sin_respaldo=[round(c, 4) for c in huerfanas],
        promesas_detectadas=promesas,
        milisegundos=transcurrido,
        rechazada=respuesta.rechazada,
        motivo=respuesta.motivo_rechazo,
        fallos=fallos,
        consulta=caso.consulta,
        respuesta=respuesta.texto,
        llamada_exitosa=bool(respuesta.llamadas) and respuesta.llamadas[0].exito,
        detalle_llamada=respuesta.llamadas[0].resumen if respuesta.llamadas else "",
        guardarrailes=list(respuesta.guardarrailes_aplicados),
    )


def ejecutar() -> list[ResultadoCaso]:
    resultados = []
    for caso in CASOS:
        servicio = ServicioFalso()
        agente = construir_agente(servicio)
        resultados.append(evaluar_caso(caso, agente, servicio))
    return resultados


def informe(resultados: list[ResultadoCaso]) -> str:
    aprobados = sum(1 for r in resultados if r.aprobado)
    ruteo = sum(1 for r in resultados if r.ruteo_correcto)
    sin_huerfanas = sum(1 for r in resultados if not r.cifras_sin_respaldo)
    sin_promesas = sum(1 for r in resultados if not r.promesas_detectadas)
    total = len(resultados)
    p95 = sorted(r.milisegundos for r in resultados)[int(total * 0.95) - 1]

    lineas = [
        "EVALUACION DEL AGENTE ASESOR · 20 casos criticos",
        "=" * 62,
        f"  Casos aprobados            {aprobados}/{total}",
        f"  Ruteo de herramienta       {ruteo}/{total}",
        f"  Sin cifras sin respaldo    {sin_huerfanas}/{total}   (G-02)",
        f"  Sin promesas de retorno    {sin_promesas}/{total}   (G-03)",
        f"  Latencia del bucle p95     {p95} ms   (contra el doble)",
        "=" * 62,
        "  La latencia es la del bucle contra un doble de respuesta fija. No es",
        "  la que espera un usuario: el servicio real calcula. Ver seccion 11 de",
        "  docs/agente/AGENTE_ASESOR.md.",
        "=" * 62,
    ]
    for r in resultados:
        marca = "OK  " if r.aprobado else "FALLA"
        lineas.append(f"{marca} {r.id} · {r.categoria:<15} {r.descripcion}")
        for fallo in r.fallos:
            lineas.append(f"        - {fallo}")
    return "\n".join(lineas)


def transcripcion(resultados: list[ResultadoCaso]) -> str:
    """Que se le pregunto, que herramienta uso y que contesto, caso por caso."""
    lineas = ["", "TRANSCRIPCION DE LAS RESPUESTAS", "=" * 62]
    for r in resultados:
        if r.llamada_exitosa:
            estado = "ok"
        elif not r.herramienta_usada:
            estado = "sin herramienta"
        else:
            estado = "fallo controlado"
        lineas.append("")
        lineas.append(f"{r.id} · {r.categoria} · {r.descripcion}")
        lineas.append(f"  PREGUNTA    {r.consulta}")
        usada = r.herramienta_usada or "ninguna, contesto la politica"
        lineas.append(f"  HERRAMIENTA {usada} [{estado}]")
        if r.detalle_llamada:
            lineas.append(f"  RESULTADO   {r.detalle_llamada}")
        lineas.append(f"  GUARDARRAIL {', '.join(r.guardarrailes) or '-'}")
        for i, parrafo in enumerate(_envolver(r.respuesta, 88)):
            lineas.append(f"  {'RESPUESTA   ' if i == 0 else '            '}{parrafo}")
    return "\n".join(lineas)


def _envolver(texto: str, ancho: int) -> list[str]:
    palabras, linea, salida = texto.split(), "", []
    for palabra in palabras:
        if len(linea) + len(palabra) + 1 > ancho:
            salida.append(linea)
            linea = palabra
        else:
            linea = f"{linea} {palabra}".strip()
    if linea:
        salida.append(linea)
    return salida or [""]


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description="Arnes de evaluacion del agente")
    analizador.add_argument("--json", default=None, help="Ruta donde escribir el detalle en JSON")
    analizador.add_argument(
        "--respuestas", action="store_true",
        help="Imprime lo que el agente contesto en cada caso, con la herramienta que uso",
    )
    args = analizador.parse_args(argv)

    resultados = ejecutar()
    print(informe(resultados))
    if args.respuestas:
        print(transcripcion(resultados))
    if args.json:
        Path(args.json).write_text(
            json.dumps([asdict(r) for r in resultados], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nDetalle escrito en {args.json}")
    return 0 if all(r.aprobado for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
