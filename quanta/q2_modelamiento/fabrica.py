"""Fabrica y registro de estrategias (Factory Method + Registry).

Gamma et al. (1994): "define una interfaz para crear un objeto, pero deja que
las subclases decidan que clase instanciar". En su forma de registro es lo que
Fowler (2002) llama Registry.

Anadir una arquitectura = registrarla aqui. Ni el servicio (cuanto 3) ni el
cliente (cuanto 4) se enteran: esa opacidad es el Patron Strategy en operacion.

La fabrica es ademas quien arma la cadena de decoradores segun configuracion,
de modo que activar la auditoria (CTRL-05) o el cache no requiere tocar ninguna
estrategia.
"""

from __future__ import annotations

import os
from functools import lru_cache

from q2_modelamiento.contrato import EstrategiaPredictiva
from q2_modelamiento.decoradores import EstrategiaAuditada, EstrategiaConCache
from q2_modelamiento.estrategias import EstrategiaDesagregada, EstrategiaGlobal


class EstrategiaNoRegistrada(ValueError):
    pass


class FabricaDeEstrategias:
    """Punto unico de construccion. Instanciable para que las pruebas puedan
    registrar dobles sin contaminar el registro global."""

    def __init__(self) -> None:
        self._registro: dict[str, type[EstrategiaPredictiva]] = {}

    def registrar(self, clase: type[EstrategiaPredictiva]) -> type[EstrategiaPredictiva]:
        """Usable tambien como decorador de clase."""
        self._registro[clase.nombre] = clase
        return clase

    def disponibles(self) -> list[str]:
        return sorted(self._registro)

    def crear(
        self,
        nombre: str | None = None,
        *,
        auditar: bool | None = None,
        cachear: bool | None = None,
        sumidero_auditoria=None,
    ) -> EstrategiaPredictiva:
        clave = nombre or os.getenv("MOTOR_POR_DEFECTO", "desagregado")
        if clave not in self._registro:
            raise EstrategiaNoRegistrada(
                f"Estrategia '{clave}' no registrada. Disponibles: {self.disponibles()}"
            )

        estrategia: EstrategiaPredictiva = self._registro[clave]()

        if auditar if auditar is not None else _bandera("XAI_AUDITAR_INFERENCIAS", True):
            estrategia = EstrategiaAuditada(estrategia, sumidero=sumidero_auditoria)
        if cachear if cachear is not None else _bandera("XAI_CACHE_ACTIVO", True):
            estrategia = EstrategiaConCache(estrategia)

        return estrategia


def _bandera(variable: str, defecto: bool) -> bool:
    valor = os.getenv(variable)
    return defecto if valor is None else valor.strip().lower() in {"1", "true", "si", "yes"}


# --- registro global ------------------------------------------------------

fabrica = FabricaDeEstrategias()
fabrica.registrar(EstrategiaDesagregada)
fabrica.registrar(EstrategiaGlobal)


def estrategias_disponibles() -> list[str]:
    return fabrica.disponibles()


@lru_cache(maxsize=8)
def obtener_estrategia(nombre: str | None = None) -> EstrategiaPredictiva:
    """Funcion de conveniencia cacheada por proceso."""
    return fabrica.crear(nombre)
