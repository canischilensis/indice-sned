"""Aislamiento del entorno para las pruebas unitarias del cuanto 5.

Nace de un fallo reproducible: `pytest -q` pasaba en una terminal y fallaba en
otra, sobre el mismo commit. La causa era la precedencia declarada en
`q5_agente.config` —variable del proceso por encima del archivo .env—, correcta
en operacion y contaminante en pruebas: una sesion que hubiera exportado
AGENTE_PROVEEDOR para levantar el servicio hacia fallar a una prueba que escribe
su propio .env temporal y espera leerlo.

El resultado de una suite no puede depender de la shell que la lanza. Una prueba
cuyo veredicto cambia con el entorno no verifica: coincide.

Es la segunda vez que el entorno de la maquina se cuela en la suite. La primera
fue mas grave —los subprocesos de tests/arquitectura heredaban el .env de la
raiz y salian a internet con la clave de quien ejecutara— y se corrigio fijando
el proveedor determinista. Aquella correccion cubrio los subprocesos; esta cubre
el proceso de pytest.

La lista de variables no se escribe a mano: se deriva de los campos de
ConfiguracionDelAgente. Un campo nuevo queda protegido sin que nadie tenga que
acordarse, que es la unica forma de proteccion que sobrevive al tiempo.
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from q5_agente.config import ConfiguracionDelAgente

#: Credenciales de proveedor. No son campos de la configuracion —a proposito, la
#: clave no debe poder filtrarse por un repr— y por eso hay que nombrarlas aqui.
_CREDENCIALES = (
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
)


def variables_de_configuracion() -> tuple[str, ...]:
    """Nombres de entorno que `ConfiguracionDelAgente` consulta, mas las claves."""
    del_dataclass = tuple(campo.name.upper() for campo in fields(ConfiguracionDelAgente))
    return del_dataclass + _CREDENCIALES


@pytest.fixture(autouse=True)
def entorno_del_agente_aislado(monkeypatch):
    """Retira del proceso toda variable del cuanto 5 antes de cada prueba.

    `monkeypatch` restaura el entorno al terminar, de modo que el aislamiento no
    se propaga fuera de la prueba ni afecta a otras suites.
    """
    for variable in variables_de_configuracion():
        monkeypatch.delenv(variable, raising=False)
