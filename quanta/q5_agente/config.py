"""Configuracion del cuanto 5. Todo por variable de entorno, nada codificado.

Deliberadamente **sin dependencias de terceros**. El cuanto 3 usa
pydantic-settings porque ya es un servicio con FastAPI y Pydantic dentro; aqui
seria una dependencia impuesta a la consola, que no la necesita para nada.

La consecuencia es concreta y se comprueba con una prueba: `scripts/asesor.py`
arranca en un Python que solo tenga httpx instalado. Un cuanto que se declara
retirable no puede arrastrar media pila de la aplicacion para imprimir una
linea en la consola.

Precedencia: variable de entorno del proceso > archivo .env de la raiz > valor
por defecto declarado abajo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

_CIERTOS = {"1", "true", "t", "si", "sí", "yes", "y", "on"}
_FALSOS = {"0", "false", "f", "no", "n", "off"}


def _leer_env(ruta: Path) -> dict[str, str]:
    """Lector minimo de .env: KEY=VALOR, con almohadillas y comillas toleradas."""
    if not ruta.is_file():
        return {}
    valores: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8", errors="ignore").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or "=" not in limpia:
            continue
        clave, _, valor = limpia.partition("=")
        valor = valor.split(" #", 1)[0].strip().strip('"').strip("'")
        valores[clave.strip().upper()] = valor
    return valores


def _a_bool(texto: str, defecto: bool) -> bool:
    minuscula = texto.strip().lower()
    if minuscula in _CIERTOS:
        return True
    if minuscula in _FALSOS:
        return False
    return defecto


@dataclass(frozen=True)
class ConfiguracionDelAgente:
    """Parametros de operacion del agente. Los nombres son los del entorno."""

    #: Servicio del indice (Q3). El agente lo consulta como cualquier usuario.
    agente_base_url: str = "http://127.0.0.1:8000"
    agente_prefijo_api: str = "/api/v1"
    agente_usuario: str = "sostenedor.demo"
    agente_clave: str = "demo"
    agente_segundos_espera: float = 10.0

    #: Proveedor de lenguaje: determinista | anthropic | openai
    agente_proveedor: str = "determinista"
    agente_modelo: str = ""

    #: Bucle y cortacircuitos (ADR-006)
    agente_max_pasos: int = 3
    agente_umbral_fallos: int = 3
    agente_segundos_reposo: float = 30.0

    #: Guardarrailes. Se apagan solo en pruebas, nunca en operacion.
    agente_guardarrail_cifras: bool = True
    agente_guardarrail_promesas: bool = True

    def con(self, **cambios: object) -> ConfiguracionDelAgente:
        """Copia con campos sustituidos. Sustituye a model_copy de Pydantic."""
        return replace(self, **cambios)  # type: ignore[arg-type]

    @classmethod
    def desde_entorno(cls, archivo_env: Path | None = None) -> ConfiguracionDelAgente:
        del_archivo = _leer_env(archivo_env if archivo_env is not None else RAIZ / ".env")
        valores: dict[str, object] = {}

        for campo in fields(cls):
            clave = campo.name.upper()
            bruto = os.environ.get(clave, del_archivo.get(clave))
            if bruto is None or bruto == "":
                continue
            defecto = campo.default
            try:
                if isinstance(defecto, bool):
                    valores[campo.name] = _a_bool(bruto, defecto)
                elif isinstance(defecto, int):
                    valores[campo.name] = int(bruto)
                elif isinstance(defecto, float):
                    valores[campo.name] = float(bruto)
                else:
                    valores[campo.name] = bruto
            except ValueError:
                # Un valor mal escrito no debe tumbar el arranque: se conserva
                # el defecto y el problema queda visible en la ruta de salud.
                continue
        return cls(**valores)  # type: ignore[arg-type]


@lru_cache(maxsize=1)
def config_agente() -> ConfiguracionDelAgente:
    return ConfiguracionDelAgente.desde_entorno()


def secreto(nombre: str, archivo_env: Path | None = None) -> str | None:
    """Credencial de un proveedor, del entorno o del .env, con la misma precedencia.

    Deliberadamente **fuera** de ConfiguracionDelAgente. Las claves de proveedor
    no son parametros de operacion: no deben viajar en el objeto que la ruta de
    salud describe ni aparecer en una traza. Se leen donde se necesitan y no se
    guardan.

    Existe por un defecto real: `.env.example` documentaba GEMINI_API_KEY en el
    .env, pero el adaptador consultaba solo os.environ, de modo que la clave
    puesta en el archivo se ignoraba en silencio y el agente respondia que
    faltaba una variable que el usuario ya habia escrito.
    """
    del_proceso = os.environ.get(nombre)
    if del_proceso:
        return del_proceso
    del_archivo = _leer_env(archivo_env if archivo_env is not None else RAIZ / ".env")
    return del_archivo.get(nombre.upper()) or None
