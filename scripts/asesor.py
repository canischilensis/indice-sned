"""Lanzador del agente asesor desde la raiz del repositorio.

Existe por la misma razon que `uvicorn --app-dir quanta`: los cuantos viven en
`quanta/`, que no esta en la ruta de Python salvo que algo la ponga. pytest lo
hace por el `pythonpath` de pyproject.toml y uvicorn por su bandera; una
invocacion con `python -m` no tiene ninguna de las dos.

    python scripts/asesor.py --rbd 25520 --trazas "por que se cae la superacion"

Equivale a `python -m q5_agente.cli` con PYTHONPATH=quanta, sin obligar a
recordar la variable de entorno.

La consola necesita httpx y nada mas: la configuracion del cuanto 5 no usa
pydantic-settings a proposito. Si aun asi falta algo, este lanzador lo dice en
una linea en lugar de mostrar una traza de importacion.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
QUANTA = RAIZ / "quanta"
if str(QUANTA) not in sys.path:
    sys.path.insert(0, str(QUANTA))

try:
    from q5_agente.cli import main
except ImportError as exc:  # dependencia ausente o entorno equivocado
    faltante = getattr(exc, "name", None)
    cabeza = (
        f"No se pudo iniciar el agente: falta el modulo '{faltante}'."
        if faltante
        else "No se pudo iniciar el agente: falta una dependencia."
    )
    print(
        f"{cabeza}\n"
        f"Detalle: {exc}\n"
        f"Interprete en uso: {sys.executable}\n"
        "Si trabaja con entorno virtual, activelo antes: .\\env\\Scripts\\Activate.ps1\n"
        "Para instalar lo necesario: pip install -r requirements-agente.txt",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

if __name__ == "__main__":
    raise SystemExit(main())
