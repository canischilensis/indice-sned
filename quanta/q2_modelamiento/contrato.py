"""Contrato del Patron Strategy (Freeman et al., 2004).

Este modulo define la unica superficie que la capa de servicio (cuanto 3)
puede tocar. Sustituir el motor de arboles por una red neuronal, o el motor
desagregado por el global, no debe requerir ningun cambio aguas arriba.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Objetos de transferencia (agnosticos de la libreria de ML)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContribucionVariable:
    """Aporte de una variable a una prediccion concreta (valor de Shapley)."""

    variable: str
    etiqueta: str
    valor: float | None
    contribucion: float

    @property
    def direccion(self) -> str:
        return "positiva" if self.contribucion >= 0 else "negativa"


@dataclass(frozen=True)
class ExplicacionLocal:
    """Descomposicion de una prediccion individual.

    Invariante de Shapley: valor_base + sum(contribuciones) == prediccion.
    """

    prediccion: float
    valor_base: float
    contribuciones: list[ContribucionVariable]

    def verificar_aditividad(self, tolerancia: float = 1e-3) -> bool:
        suma = self.valor_base + sum(c.contribucion for c in self.contribuciones)
        return abs(suma - self.prediccion) <= tolerancia


@dataclass(frozen=True)
class CurvaSensibilidad:
    """Curva ICE: respuesta de la prediccion al recorrer una variable."""

    variable: str
    valores: list[float]
    predicciones: list[float]
    valor_actual: float | None = None
    prediccion_actual: float | None = None

    @property
    def es_monotona_creciente(self) -> bool:
        return all(b >= a - 1e-9 for a, b in zip(self.predicciones, self.predicciones[1:]))


@dataclass(frozen=True)
class Prediccion:
    """Resultado de una inferencia sobre el Indice SNED."""

    indice: float
    factores: dict[str, float] = field(default_factory=dict)
    estrategia: str = ""
    version_modelo: str = ""
    incertidumbre_mae: float | None = None


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------


class EstrategiaPredictiva(ABC):
    """Interfaz estable del motor predictivo."""

    nombre: str = "abstracta"
    version: str = "0.0.0"
    soporta_explicabilidad: bool = False
    soporta_desglose_por_factor: bool = False

    @property
    @abstractmethod
    def variables_requeridas(self) -> list[str]:
        """Nombres de las variables de entrada que la estrategia consume."""

    @abstractmethod
    def predecir(self, observacion: dict[str, float | str | None]) -> Prediccion:
        """Estima el Indice SNED para un establecimiento-periodo."""

    def explicar(self, observacion: dict, factor: str | None = None) -> ExplicacionLocal:
        raise NotImplementedError(f"{self.nombre} no implementa explicabilidad local.")

    def simular(
        self,
        observacion: dict,
        variable: str,
        rango: list[float] | None = None,
        n_puntos: int = 25,
    ) -> CurvaSensibilidad:
        raise NotImplementedError(f"{self.nombre} no implementa analisis contrafactual.")

    def describir(self) -> dict:
        return {
            "nombre": self.nombre,
            "version": self.version,
            "explicabilidad": self.soporta_explicabilidad,
            "desglose_por_factor": self.soporta_desglose_por_factor,
            "n_variables": len(self.variables_requeridas),
        }
