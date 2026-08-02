"""Prueba de arquitectura: las fronteras entre cuantos son ejecutables."""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_el_servicio_no_importa_librerias_de_machine_learning():
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "verificar_arquitectura.py")],
        capture_output=True, text=True,
    )
    assert resultado.returncode == 0, resultado.stdout
