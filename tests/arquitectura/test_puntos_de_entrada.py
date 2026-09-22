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
    """Reproduce una consola recien abierta: sin PYTHONPATH heredado.

    Fija ademas el proveedor determinista, y no es un detalle. Estas pruebas
    lanzan la consola como subproceso, que lee el `.env` de la raiz; con un
    proveedor externo configurado ahi, la suite salia a internet y **gastaba la
    clave de quien la ejecutara**. Ademas la volvia dependiente de la redaccion
    de un modelo: la prueba se cayo porque Gemini escribio "problema de
    conexion" donde el determinista escribe "no fue posible conectar".

    Lo que estas pruebas verifican es el punto de entrada y la traduccion de un
    fallo de transporte. Nada de eso necesita un modelo de lenguaje.
    """
    entorno = dict(os.environ)
    entorno.pop("PYTHONPATH", None)
    entorno["AGENTE_PROVEEDOR"] = "determinista"
    entorno["AGENTE_MODELO"] = ""
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


# Modulos que la consola NO debe necesitar. pydantic-settings y FastAPI viven en
# el servicio; los SDK de los proveedores se importan de forma perezosa, dentro
# del adaptador que los usa. La consola solo necesita httpx. Si algun dia alguien
# los importa desde la cadena del CLI, esta prueba lo detiene.
_PROHIBIDOS_EN_LA_CONSOLA = (
    "pydantic_settings",
    "pydantic",
    "fastapi",
    "anthropic",
    "openai",
    "google",
)

_GUION_SIN_DEPENDENCIAS = """
import sys
from pathlib import Path

BLOQUEADOS = {bloqueados}

class Bloqueador:
    def find_spec(self, nombre, ruta=None, destino=None):
        if nombre.split(".")[0] in BLOQUEADOS:
            raise ImportError("bloqueado por la prueba: " + nombre)
        return None

sys.meta_path.insert(0, Bloqueador())
sys.path.insert(0, str(Path({raiz!r}) / "quanta"))
import q5_agente.cli  # noqa: F401
import q5_agente.fabrica  # noqa: F401
print("ARRANQUE OK")
"""


def test_la_consola_no_necesita_pydantic_settings_ni_fastapi():
    """La configuracion del cuanto 5 es de biblioteca estandar, a proposito.

    Nace de un fallo real: `scripts/asesor.py` reventaba con ModuleNotFoundError
    de pydantic_settings en un interprete que no tenia instaladas las
    dependencias del servicio. Un cuanto que se declara retirable no puede
    arrastrar media pila de la aplicacion para imprimir una linea en consola.
    """
    guion = _GUION_SIN_DEPENDENCIAS.format(
        bloqueados=set(_PROHIBIDOS_EN_LA_CONSOLA), raiz=str(RAIZ)
    )
    resultado = subprocess.run(
        [sys.executable, "-c", guion],
        cwd=RAIZ, env=_entorno_limpio(), capture_output=True, text=True, timeout=120,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "ARRANQUE OK" in resultado.stdout


def test_el_lanzador_explica_la_dependencia_ausente_en_vez_de_mostrar_una_traza():
    """Si el interprete es el equivocado, el mensaje debe decir cual y que hacer."""
    guion = (
        "import sys, runpy\n"
        "class Bloqueador:\n"
        "    def find_spec(self, nombre, ruta=None, destino=None):\n"
        "        if nombre.split('.')[0] == 'httpx':\n"
        "            raise ImportError('bloqueado por la prueba: httpx')\n"
        "        return None\n"
        "sys.meta_path.insert(0, Bloqueador())\n"
        "sys.argv = ['asesor.py', '--help']\n"
        "runpy.run_path('scripts/asesor.py', run_name='__main__')\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", guion],
        cwd=RAIZ, env=_entorno_limpio(), capture_output=True, text=True, timeout=120,
    )
    assert "No se pudo iniciar el agente" in resultado.stderr
    assert "httpx" in resultado.stderr
    assert "Interprete en uso" in resultado.stderr


def test_la_consola_avisa_en_vez_de_reventar_si_el_servicio_no_esta():
    """Un servicio apagado es una condicion esperable, no un error de programa.

    Lo que se exige es el comportamiento —avisar de un problema de conexion sin
    traza y sin cifras— y no una frase textual. La redaccion depende del
    proveedor, y clavar una frase concreta convierte una prueba de arquitectura
    en una prueba de estilo.
    """
    entorno = _entorno_limpio()
    # Puerto sin nadie escuchando: fuerza el fallo de transporte.
    entorno["AGENTE_BASE_URL"] = "http://127.0.0.1:9"
    resultado = subprocess.run(
        [sys.executable, "scripts/asesor.py", "--rbd", "25520", "dame el diagnostico"],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, timeout=120,
    )
    salida = resultado.stdout.lower()
    assert "Traceback" not in resultado.stderr, resultado.stderr
    assert "ConnectError" not in resultado.stdout + resultado.stderr
    assert "httpx" not in salida, "la biblioteca no es asunto del usuario"
    assert any(p in salida for p in ("conectar", "conexion", "conexión")), salida
    assert any(
        p in salida for p in ("no puedo", "no est", "no hay", "no fue posible")
    ), "debe declarar que el dato no llego, en vez de responder igual"
