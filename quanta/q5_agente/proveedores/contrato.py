"""Puerto ProveedorDeModelo.

Aisla una sola dimension de cambio: quien completa el texto. Anthropic, OpenAI y
el proveedor determinista son adaptadores del mismo contrato, y el bucle no sabe
cual esta enchufado.

Nota deliberada sobre el proveedor determinista: no es un modelo de lenguaje.
Existe para que el bucle, las herramientas y los guardarrailes puedan verificarse
sin credenciales, sin red y dentro de la suite. La calidad de la redaccion de un
modelo real es otra medicion, y esta declarada como pendiente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Mensaje:
    rol: str  # "sistema" | "usuario" | "herramienta" | "asistente"
    contenido: str


@dataclass
class PeticionDeHerramienta:
    nombre: str
    parametros: dict[str, Any] = field(default_factory=dict)


@dataclass
class RespuestaDelModelo:
    """O el modelo pide una herramienta, o entrega el texto final."""

    texto: str | None = None
    peticion: PeticionDeHerramienta | None = None
    tokens_entrada: int = 0
    tokens_salida: int = 0

    @property
    def quiere_herramienta(self) -> bool:
        return self.peticion is not None


class ProveedorDeModelo(ABC):
    """Puerto del proveedor de completado."""

    nombre: str = "sin_nombre"
    #: Precio por millon de tokens, para instrumentar costo desde el primer dia.
    usd_por_millon_entrada: float = 0.0
    usd_por_millon_salida: float = 0.0

    @abstractmethod
    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        """Devuelve el siguiente paso: una peticion de herramienta o el texto."""

    def costo(self, tokens_entrada: int, tokens_salida: int) -> float:
        return round(
            tokens_entrada / 1_000_000 * self.usd_por_millon_entrada
            + tokens_salida / 1_000_000 * self.usd_por_millon_salida,
            8,
        )

    def describir(self) -> dict[str, Any]:
        return {"proveedor": self.nombre}
