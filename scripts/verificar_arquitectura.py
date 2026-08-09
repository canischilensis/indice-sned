"""Compuerta de arquitectura: las fronteras entre cuantos son ejecutables.

Dos familias de reglas:

1. LIBRERIAS PROHIBIDAS por cuanto. El cuanto 3 (servicio) no puede importar
   scikit-learn, TensorFlow ni shap: si lo hace, el Patron Strategy dejo de
   sostenerse y cambiar de algoritmo volvera a requerir tocar la presentacion.

2. DEPENDENCIAS ENTRE CUANTOS. El grafo permitido es estrictamente:
       q1 -> compartido
       q2 -> compartido
       q3 -> q2, compartido
       q4 -> (solo HTTP, nada de Python)
       q5 -> compartido
   Cualquier arista fuera de ese grafo es una violacion.

   El cuanto 5 es el caso mas estricto: consulta el servicio por HTTP como
   cualquier usuario, de modo que NO puede importar q3_servicio ni
   q2_modelamiento. Si lo hiciera, eludiria CTRL-04 y dejaria de ser un
   cuanto retirable.

    python scripts/verificar_arquitectura.py
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

LIBRERIAS_PROHIBIDAS = {
    "q3_servicio": {"sklearn", "tensorflow", "keras", "shap", "joblib", "xgboost"},
    "q1_ingesta": {"fastapi", "sklearn", "tensorflow", "shap"},
    "compartido": {"fastapi", "sklearn", "tensorflow", "shap", "pandas"},
    # El agente no calcula ni persiste: si importara alguna de estas, habria
    # dejado de orquestar para empezar a duplicar el dominio.
    "q5_agente": {
        "sklearn", "tensorflow", "keras", "shap", "joblib", "xgboost",
        "sqlalchemy", "psycopg", "psycopg2", "pandas", "numpy",
    },
}

DEPENDENCIAS_PERMITIDAS = {
    "q1_ingesta": {"compartido"},
    "q2_modelamiento": {"compartido"},
    "q3_servicio": {"q2_modelamiento", "compartido"},
    "q5_agente": {"compartido"},
    "compartido": set(),
}

CUANTOS = set(DEPENDENCIAS_PERMITIDAS)
PATRON = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_.]+)", re.MULTILINE)


def main() -> int:
    violaciones: list[str] = []

    for cuanto in CUANTOS:
        carpeta = RAIZ / "quanta" / cuanto
        if not carpeta.exists():
            continue
        prohibidas = LIBRERIAS_PROHIBIDAS.get(cuanto, set())
        permitidas = DEPENDENCIAS_PERMITIDAS[cuanto]

        for archivo in carpeta.rglob("*.py"):
            for modulo in PATRON.findall(archivo.read_text(encoding="utf-8")):
                raiz_modulo = modulo.split(".")[0]
                rel = archivo.relative_to(RAIZ)

                if raiz_modulo in prohibidas:
                    violaciones.append(f"{rel}: libreria '{modulo}' prohibida en el cuanto {cuanto}")

                if raiz_modulo in CUANTOS and raiz_modulo != cuanto and raiz_modulo not in permitidas:
                    violaciones.append(
                        f"{rel}: el cuanto {cuanto} no puede depender de {raiz_modulo}"
                    )

    if violaciones:
        print("FRONTERA DE CUANTOS VIOLADA:")
        for v in sorted(set(violaciones)):
            print(f"  - {v}")
        return 1

    print("Fronteras de cuantos respetadas.")
    print(
        "  grafo permitido: q1 -> compartido | q2 -> compartido | "
        "q3 -> q2, compartido | q5 -> compartido"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
