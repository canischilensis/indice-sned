"""Consola del agente.

    python -m q5_agente.cli --rbd 25520 "por que se me cae la superacion"
    python -m q5_agente.cli --rbd 25520 --proveedor anthropic "que conviene mover primero"

Requiere el servicio del indice levantado. Si no lo esta, el agente lo dira sin
inventar cifras, que es exactamente el comportamiento esperado.
"""

from __future__ import annotations

import argparse
import sys

from q5_agente.config import config_agente
from q5_agente.contrato import Consulta
from q5_agente.errores import ErrorDelAgente
from q5_agente.fabrica import crear_agente


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description="Asesor de gestion del Indice SNED")
    analizador.add_argument("texto", help="La consulta del equipo directivo")
    analizador.add_argument("--rbd", required=True, help="RBD bajo jurisdiccion del usuario")
    analizador.add_argument("--periodo", default=None, help="Bienio, por ejemplo 2024-2025")
    analizador.add_argument("--proveedor", default=None, help="determinista | anthropic | openai")
    analizador.add_argument(
        "--trazas", action="store_true", help="Muestra las llamadas y el costo"
    )
    args = analizador.parse_args(argv)

    cfg = config_agente()
    if args.proveedor:
        cfg = cfg.model_copy(update={"agente_proveedor": args.proveedor})

    try:
        agente = crear_agente(cfg)
        respuesta = agente.asesorar(
            Consulta(
                texto=args.texto,
                rbd=args.rbd,
                periodo=args.periodo,
                usuario=cfg.agente_usuario,
            )
        )
    except ErrorDelAgente as exc:
        print(f"El agente no pudo responder: {exc}", file=sys.stderr)
        return 1

    print(respuesta.texto)
    if args.trazas:
        print("\n--- trazabilidad ---")
        for llamada in respuesta.llamadas:
            estado = "ok" if llamada.exito else "fallo"
            print(
                f"  {llamada.herramienta} [{estado}] "
                f"{llamada.milisegundos} ms · {llamada.resumen}"
            )
        print(
            f"  tokens: {respuesta.uso.tokens_entrada} entrada / "
            f"{respuesta.uso.tokens_salida} salida · costo USD {respuesta.uso.costo_usd:.6f}"
        )
        print(f"  guardarrailes: {', '.join(respuesta.guardarrailes_aplicados)}")
        if respuesta.rechazada:
            print(f"  RECHAZADA: {respuesta.motivo_rechazo}")
    return 2 if respuesta.rechazada else 0


if __name__ == "__main__":
    raise SystemExit(main())
