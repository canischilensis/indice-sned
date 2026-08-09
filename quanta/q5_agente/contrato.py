"""Puerto AsesorDeGestion y sus objetos de valor.

El cuanto 5 se enchufa al ecosistema por este puerto, del mismo modo en que
RepositorioEstablecimientos gobierna sus dos adaptadores. Si se retira, el
sistema sigue operando: ningun otro cuanto importa este modulo.

Principio rector, no negociable y verificado por prueba: el agente orquesta y
traduce; el motor predictivo calcula; el equipo directivo decide. El modelo de
lenguaje no computa el indice ni pondera factores.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Consulta:
    """Lo que el equipo directivo pregunta, junto a su contexto de sesion."""

    texto: str
    rbd: str
    periodo: str | None = None
    usuario: str = "anonimo"


@dataclass(frozen=True)
class LlamadaHerramienta:
    """Registro de una invocacion. Es la unidad de trazabilidad del agente."""

    herramienta: str
    parametros: dict[str, Any]
    exito: bool
    resumen: str
    milisegundos: int = 0


@dataclass(frozen=True)
class Uso:
    """Consumo del proveedor. Se instrumenta desde el primer dia, no despues."""

    tokens_entrada: int = 0
    tokens_salida: int = 0
    costo_usd: float = 0.0
    llamadas_al_modelo: int = 0

    def mas(self, otro: Uso) -> Uso:
        return Uso(
            tokens_entrada=self.tokens_entrada + otro.tokens_entrada,
            tokens_salida=self.tokens_salida + otro.tokens_salida,
            costo_usd=round(self.costo_usd + otro.costo_usd, 8),
            llamadas_al_modelo=self.llamadas_al_modelo + otro.llamadas_al_modelo,
        )


@dataclass
class RespuestaAsesor:
    """Salida del agente: texto, trazabilidad y veredicto de los guardarrailes."""

    texto: str
    llamadas: list[LlamadaHerramienta] = field(default_factory=list)
    uso: Uso = field(default_factory=Uso)
    cifras_citadas: list[float] = field(default_factory=list)
    guardarrailes_aplicados: list[str] = field(default_factory=list)
    rechazada: bool = False
    motivo_rechazo: str | None = None

    @property
    def fundada_en_herramientas(self) -> bool:
        """Verdadero si toda cifra citada provino de una respuesta de herramienta."""
        return not self.rechazada and any(ll.exito for ll in self.llamadas)


class AsesorDeGestion(ABC):
    """Puerto del cuanto 5.

    Aisla una sola dimension de cambio: la forma de razonar sobre las
    herramientas del servicio. Un bucle simple y un planificador explicito son
    dos adaptadores del mismo puerto.
    """

    nombre: str = "sin_nombre"

    @abstractmethod
    def asesorar(self, consulta: Consulta) -> RespuestaAsesor:
        """Responde la consulta usando exclusivamente datos de herramientas."""

    def describir(self) -> dict[str, Any]:
        return {"asesor": self.nombre}
