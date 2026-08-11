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

    #: Modelo local servido por Ollama. Sin clave y sin salida a internet: el
    #: dato del establecimiento no abandona la maquina, que en este dominio es
    #: un argumento de politica de datos y no una optimizacion de costo.
    agente_ollama_url: str = "http://127.0.0.1:11434"
    #: Modelo local, en su PROPIO campo y no en AGENTE_MODELO.
    #:
    #: Nace de un defecto real del 2026-08-10: AGENTE_MODELO era una sola
    #: variable compartida por cuatro proveedores. Al cambiar de proveedor sin
    #: cambiar de modelo, el modelo del anterior se filtraba al nuevo, y una
    #: evaluacion entera de veinte casos se fue al suelo pidiendole a Ollama un
    #: modelo de Google. Un valor correcto para un proveedor no es un valor
    #: correcto para otro, y compartir el campo lo daba por supuesto.
    agente_ollama_modelo: str = "qwen3:8b"
    #: Tres minutos, no diez segundos. En CPU un paso puede tardar mas de un
    #: minuto, y un tiempo de espera corto convertiria la lentitud esperada en un
    #: fallo del proveedor: dos conclusiones distintas y una equivocada.
    agente_ollama_espera: float = 180.0

    #: Adaptador del puerto AsesorDeGestion: bucle_simple | langgraph_react
    #:
    #: El predeterminado es el bucle escrito a mano, que no necesita mas que
    #: httpx. `langgraph_react` arrastra la pila de LangChain y se carga de forma
    #: perezosa, solo si se pide. Existen los dos para poder medir la diferencia.
    agente_orquestador: str = "bucle_simple"

    #: Bucle y cortacircuitos (ADR-006)
    agente_max_pasos: int = 3
    agente_umbral_fallos: int = 3
    agente_segundos_reposo: float = 30.0

    #: Guardarrailes. Se apagan solo en pruebas, nunca en operacion.
    agente_guardarrail_cifras: bool = True
    agente_guardarrail_promesas: bool = True

    #: Origenes admitidos por CORS, separados por coma.
    #:
    #: Estaban escritos a mano dentro de `app.py`. Funcionaba mientras el cliente
    #: viviera en 127.0.0.1:5173 y dejaba de funcionar en cuanto dejara de
    #: hacerlo, que es exactamente lo que ocurre al contenerizar: el navegador
    #: pide desde el puerto publicado del contenedor del cliente y ese origen no
    #: estaba en la lista. Una direccion de red no es una constante del programa.
    agente_cors_origenes: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origenes(self) -> list[str]:
        """La lista, ya separada y sin entradas vacias."""
        return [o.strip() for o in self.agente_cors_origenes.split(",") if o.strip()]

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
