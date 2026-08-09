"""Los puntos de entrada del cuanto 5 funcionan fuera de pytest.

Existe por un defecto real: el arnes de evaluacion y la consola importaban
`q5_agente` sin que nada pusiera `quanta/` en la ruta de Python. Dentro de
pytest funcionaba, porque `pythonpath` de pyproject.toml lo resuelve; ejecutados
a mano desde la raiz del repositorio, fallaban con ModuleNotFoundError.

Estas pruebas invocan los puntos de entrada como subprocesos, desde la raiz y
**con PYTHONPATH borrado**, que es exactamente la condicion del usuario.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.agente


def _entorno_limpio() -> dict[str, str]:
    """Reproduce una consola recien abierta: sin PYTHONPATH heredado."""
    entorno = dict(os.environ)
    entorno.pop("PYTHONPATH", None)
    return entorno


def test_el_arnes_de_evaluacion_corre_desde_la_raiz():
    resultado = subprocess.run(
        [sys.executable, "tests/evaluacion/arnes.py"],
        cwd=RAIZ, env=_entorno_limpio(), capture_output=True, text=True, timeout=180,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "Casos aprobados" in resultado.stdout
    assert "ModuleNotFoundError" not in resultado.stderr


def test_la_consola_del_agente_arranca_desde_la_raiz():
    resultado = subprocess.run(
        [sys.executable, "scripts/asesor.py", "--help"],
        cwd=RAIZ, env=_entorno_limpio(), capture_output=True, text=True, timeout=120,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "--rbd" in resultado.stdout
    assert "ModuleNotFoundError" not in resultado.stderr


def test_la_consola_avisa_en_vez_de_reventar_si_el_servicio_no_esta():
    """Un servicio apagado es una condicion esperable, no un error de programa."""
    entorno = _entorno_limpio()
    # Puerto sin nadie escuchando: fuerza el fallo de transporte.
    entorno["AGENTE_BASE_URL"] = "http://127.0.0.1:9"
    resultado = subprocess.run(
        [sys.executable, "scripts/asesor.py", "--rbd", "25520", "dame el diagnostico"],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, timeout=120,
    )
    assert "Traceback" not in resultado.stderr, resultado.stderr
    assert "ConnectError" not in resultado.stdout + resultado.stderr
    assert "no fue posible conectar" in resultado.stdout.lower()
