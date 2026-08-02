"""Puerto Repositorio (Fowler, 2002).

"Media entre el dominio y las capas de mapeo de datos usando una interfaz
similar a una coleccion para acceder a los objetos de dominio."

Antes de este puerto, la capa de servicio ejecutaba `pd.read_parquet()` y por
tanto conocia el formato de almacenamiento. El diseno declara PostgreSQL como
entregable formal con tres vistas de consumo: existian dos origenes posibles
para el mismo dato y el servicio estaba acoplado a uno.

El servicio ahora pide `repositorio.obtener(rbd, periodo)` y deja de saber si
detras hay un archivo o una base de datos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ConjuntoNoDisponible(RuntimeError):
    """El origen de datos no esta accesible."""


class EstablecimientoNoEncontrado(KeyError):
    """El RBD no existe en el conjunto analitico."""


class RepositorioEstablecimientos(ABC):
    """Interfaz similar a una coleccion sobre el conjunto analitico."""

    origen: str = "abstracto"

    @abstractmethod
    def obtener(self, rbd: str, periodo: str | None = None) -> dict:
        """Variables de gestion de un establecimiento-periodo.

        Lanza EstablecimientoNoEncontrado si el RBD no existe.
        """

    @abstractmethod
    def listar(self, rbds: list[str], limite: int = 50) -> list[dict]:
        """Resumen de los establecimientos indicados."""

    @abstractmethod
    def ranking(self, rbd: str, periodo: str | None = None) -> dict:
        """Posicion del establecimiento dentro de su grupo homogeneo.

        Es la mecanica real de la seleccion SNED: no decide el indice absoluto
        sino la posicion relativa dentro del cluster del periodo.
        """

    @abstractmethod
    def existe(self, rbd: str) -> bool: ...

    def describir(self) -> dict:
        return {"origen": self.origen, "implementacion": type(self).__name__}
