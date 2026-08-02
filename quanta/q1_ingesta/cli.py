"""Interfaz de linea de comandos del cuanto 1.

    python -m q1_ingesta.cli inventario
    python -m q1_ingesta.cli verificar
"""

from __future__ import annotations

import sys

from q1_ingesta.fuentes import FUENTES
from compartido.rutas import DATA_PROCESSED, DATA_RAW


def inventario() -> int:
    print(f"{'CODIGO':<16}{'CARPETA':<18}{'ARCHIVOS':>9}  ORGANISMO")
    print("-" * 78)
    total = 0
    for f in FUENTES:
        carpeta = DATA_RAW / f.carpeta
        n = len(list(carpeta.glob("*"))) if carpeta.exists() else 0
        total += n
        estado = "" if carpeta.exists() else "  (carpeta ausente)"
        print(f"{f.codigo:<16}{f.carpeta:<18}{n:>9}  {f.organismo}{estado}")
    print("-" * 78)
    print(f"{len(FUENTES)} fuentes declaradas, {total} archivos en disco.")
    print(f"Meta OE1: >= 8 fuentes -> {'CUMPLE' if len(FUENTES) >= 8 else 'NO CUMPLE'}")
    return 0


def verificar() -> int:
    faltan = [f.codigo for f in FUENTES if not (DATA_RAW / f.carpeta).exists()]
    procesados = sorted(p.name for p in DATA_PROCESSED.glob("*.parquet")) if DATA_PROCESSED.exists() else []
    print(f"Fuentes crudas ausentes: {faltan or 'ninguna'}")
    print(f"Artefactos procesados: {len(procesados)}")
    for p in procesados:
        print(f"  - {p}")
    return 1 if faltan else 0


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    comando = argv[0] if argv else "inventario"
    if comando == "inventario":
        return inventario()
    if comando == "verificar":
        return verificar()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
