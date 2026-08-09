"""Lanzador del agente asesor desde la raiz del repositorio.

Existe por la misma razon que `uvicorn --app-dir quanta`: los cuantos viven en
`quanta/`, que no esta en la ruta de Python salvo que algo la ponga. pytest lo
hace por el `pythonpath` de pyproject.toml y uvicorn por su bandera; una
invocacion con `python -m` no tiene ninguna de las dos.

    python scripts/asesor.py --rbd 25520 --trazas "por que se cae la superacion"

Equivale a `python -m q5_agente.cli` con PYTHONPATH=quanta, sin obligar a
recordar la variable de entorno.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
QUANTA = RAIZ / "quanta"
if str(QUANTA) not in sys.path:
    sys.path.insert(0, str(QUANTA))

from q5_agente.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
