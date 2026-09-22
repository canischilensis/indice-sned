"""Puerto Herramienta y el resultado que toda herramienta debe devolver.

Cada herramienta envuelve rutas que ya existen y estan probadas. El agente no
calcula: pide. El resultado transporta, ademas de los datos, el conjunto de
cifras que el servicio devolvio, porque ese conjunto es lo que el guardarrail de
fundamentacion usara para aceptar o rechazar el texto generado.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


def _recolectar_cifras(nodo: Any, acumulado: set[float]) -> None:
    """Recorre la respuesta y acumula toda cifra finita que contenga."""
    if isinstance(nodo, bool):
        return
    if isinstance(nodo, (int, float)):
        if math.isfinite(float(nodo)):
            acumulado.add(round(float(nodo), 6))
        return
    if isinstance(nodo, dict):
        for valor in nodo.values():
            _recolectar_cifras(valor, acumulado)
        return
    if isinstance(nodo, (list, tuple)):
        for valor in nodo:
            _recolectar_cifras(valor, acumulado)


@dataclass
class ResultadoHerramienta:
    """Lo que una herramienta entrega al bucle.

    Distingue dos conjuntos de cifras, y la distincion importa:

    - `cifras` son magnitudes del **dato**: el indice, un aporte, un percentil.
      Son las que respaldan una afirmacion sobre el establecimiento.
    - `cifras_diagnostico` son magnitudes que aparecen en un **mensaje del
      sistema**: un RBD dentro de un 403, un puerto dentro de un error de
      conexion. No son una afirmacion sobre el establecimiento, pero tampoco
      son invencion del modelo: repetirlas literalmente es lo correcto.
    """

    herramienta: str
    datos: dict[str, Any]
    origen: str
    exito: bool = True
    error: str | None = None
    cifras: set[float] = field(default_factory=set)
    cifras_diagnostico: set[float] = field(default_factory=set)

    @classmethod
    def desde(cls, herramienta: str, datos: dict[str, Any], origen: str) -> ResultadoHerramienta:
        cifras: set[float] = set()
        _recolectar_cifras(datos, cifras)
        return cls(herramienta=herramienta, datos=datos, origen=origen, cifras=cifras)

    @classmethod
    def fallida(cls, herramienta: str, error: str) -> ResultadoHerramienta:
        from q5_agente.guardarrailes import extraer_magnitudes  # noqa: PLC0415

        return cls(
            herramienta=herramienta,
            datos={},
            origen="ninguno",
            exito=False,
            error=error,
            cifras_diagnostico=set(extraer_magnitudes(error)),
        )


class Herramienta(ABC):
    """Puerto: una capacidad que el agente puede invocar sobre el servicio."""

    nombre: str = "sin_nombre"
    descripcion: str = ""
    #: Palabras que, presentes en la consulta, hacen pertinente esta herramienta.
    disparadores: tuple[str, ...] = ()

    @abstractmethod
    def esquema(self) -> dict[str, Any]:
        """Descripcion de parametros, en el formato que los proveedores esperan."""

    @abstractmethod
    def ejecutar(self, **parametros: Any) -> ResultadoHerramienta:
        """Invoca el servicio y devuelve datos verificables."""

    def pertinencia(self, texto: str) -> int:
        """Puntaje de correspondencia con la consulta. Lo usa el ruteo local."""
        minuscula = texto.lower()
        return sum(1 for palabra in self.disparadores if palabra in minuscula)
