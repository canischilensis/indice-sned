"""Aplica esquemas, semillas y vistas sobre PostgreSQL.

    python scripts/inicializar_bd.py [--dry-run]

Orden obligatorio: esquemas -> catalogo de factores -> semillas -> vistas.

El catalogo de factores va ANTES que las semillas porque `core.tipo_indicador` y
`core.tipo_evento_sie` declaran `factor_asociado` con clave foranea hacia
`core.factor_sned`: sembrarlas primero violaria la integridad referencial.
Las vistas van al final porque dependen de todas las tablas.

Todo el DDL es idempotente (IF NOT EXISTS / CREATE OR REPLACE / ON CONFLICT),
de modo que re-ejecutarlo es seguro.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "quanta"))

ORDEN = ("esquemas", "semillas", "vistas")


def archivos_sql() -> dict[str, list[Path]]:
    return {carpeta: sorted((RAIZ / "db" / carpeta).glob("*.sql")) for carpeta in ORDEN}


def sembrar_factores(cx) -> int:
    """Puebla core.factor_sned desde el contrato compartido.

    El JSON es la fuente de verdad y la tabla su espejo: asi no pueden
    desincronizarse. El trigger de suma = 1,0 es DEFERRABLE, de modo que valida
    al confirmar la transaccion y no fila por fila.
    """
    from sqlalchemy import text

    catalogo = json.loads((RAIZ / "contratos" / "catalogo_factores.json").read_text(encoding="utf-8"))
    for f in catalogo["factores"]:
        f.setdefault("es_accionable", True)
        f.setdefault("fuente_oficial", None)
        cx.execute(
            text(
                """
                INSERT INTO core.factor_sned
                    (factor_cod, nombre, ponderacion, es_accionable,
                     fuente_oficial, restriccion, descripcion)
                VALUES (:codigo, :nombre, :peso, :es_accionable,
                        :fuente_oficial, :restriccion, :descripcion)
                ON CONFLICT (factor_cod) DO UPDATE
                   SET nombre         = EXCLUDED.nombre,
                       ponderacion    = EXCLUDED.ponderacion,
                       es_accionable  = EXCLUDED.es_accionable,
                       fuente_oficial = EXCLUDED.fuente_oficial,
                       restriccion    = EXCLUDED.restriccion,
                       descripcion    = EXCLUDED.descripcion
                """
            ),
            f,
        )
    return len(catalogo["factores"])


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    inventario = archivos_sql()

    if "--dry-run" in argv:
        for carpeta, archivos in inventario.items():
            print(f"{carpeta}:")
            for a in archivos:
                print(f"    {a.name}")
        return 0

    url = os.getenv("DATABASE_URL")
    if not url:
        print("Falta DATABASE_URL. Copia .env.example a .env y completa la cadena.")
        return 2

    from sqlalchemy import create_engine, text

    motor = create_engine(url, future=True)

    with motor.begin() as cx:
        for archivo in inventario["esquemas"]:
            print(f"  aplicando esquemas/{archivo.name}")
            cx.execute(text(archivo.read_text(encoding="utf-8")))

        n = sembrar_factores(cx)
        print(f"  core.factor_sned sembrado con {n} factores")

        for archivo in inventario["semillas"]:
            print(f"  aplicando semillas/{archivo.name}")
            cx.execute(text(archivo.read_text(encoding="utf-8")))

        for archivo in inventario["vistas"]:
            print(f"  aplicando vistas/{archivo.name}")
            cx.execute(text(archivo.read_text(encoding="utf-8")))

    print("Base de datos inicializada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
