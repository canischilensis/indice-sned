"""Aplica esquemas, semillas y vistas sobre PostgreSQL.

    python scripts/inicializar_bd.py [--dry-run]

Orden: esquemas -> validacion del contrato -> semillas -> vistas.

El DDL canonico siembra core.factor_sned en linea; este script solo VALIDA que
contratos/catalogo_factores.json coincida con la tabla y falla si difiere. Asi
el JSON sigue sirviendo de contrato al codigo Python sin ser una segunda fuente
de verdad.

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


class CatalogoDivergente(RuntimeError):
    """El contrato JSON y la tabla no coinciden."""


def validar_factores(cx) -> int:
    """Comprueba que contratos/catalogo_factores.json coincida con la tabla.

    El DDL es la FUENTE UNICA Y SIEMPRE MANDA: siembra core.factor_sned en linea.
    Este script ya no la puebla. El JSON es el contrato que consume el codigo
    Python, nunca un origen alternativo del dato: si difiere, la inicializacion
    falla y lo que se corrige es el JSON.
    """
    from sqlalchemy import text

    catalogo = json.loads((RAIZ / "contratos" / "catalogo_factores.json").read_text(encoding="utf-8"))
    en_tabla = {
        r[0]: {"ponderacion": float(r[1]), "es_accionable": bool(r[2])}
        for r in cx.execute(
            text("SELECT factor_cod, ponderacion, es_accionable FROM core.factor_sned")
        ).all()
    }

    problemas: list[str] = []
    for f in catalogo["factores"]:
        cod = f["codigo"]
        fila = en_tabla.get(cod)
        if fila is None:
            problemas.append(f"{cod}: en el JSON pero no en core.factor_sned")
            continue
        if abs(fila["ponderacion"] - float(f["peso"])) > 1e-9:
            problemas.append(
                f"{cod}: ponderacion JSON={f['peso']} tabla={fila['ponderacion']}"
            )
        if "es_accionable" in f and bool(f["es_accionable"]) != fila["es_accionable"]:
            problemas.append(
                f"{cod}: es_accionable JSON={f['es_accionable']} tabla={fila['es_accionable']}"
            )
    for cod in sorted(set(en_tabla) - {f["codigo"] for f in catalogo["factores"]}):
        problemas.append(f"{cod}: en core.factor_sned pero no en el JSON")

    if problemas:
        raise CatalogoDivergente(
            "contratos/catalogo_factores.json no coincide con core.factor_sned.\n"
            "EL DDL MANDA SIEMPRE. Corrige el JSON para que coincida con la tabla; "
            "no modifiques el DDL para acomodar el JSON.\n  - "
            + "\n  - ".join(problemas)
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

        n = validar_factores(cx)
        print(f"  core.factor_sned validado contra el contrato: {n} factores coinciden")

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
