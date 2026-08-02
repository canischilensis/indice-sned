"""Reglas de alerta como especificaciones (Evans, 2003).

Antes, `evaluar_alertas()` acumulaba condicionales dentro de una funcion. Cada
tipologia nueva la hacia crecer y ninguna era comprobable de forma aislada.

Ahora cada tipologia es un objeto con codigo, severidad y prueba unitaria
propia. Todas las reglas se evaluan siempre: no es una cadena de
responsabilidad, donde el recorrido se detiene en el primer manejador que
atiende, sino un conjunto de especificaciones de seleccion.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from compartido.especificacion import Especificacion


@dataclass(frozen=True)
class ContextoDeAlerta:
    """Candidato evaluado: la prediccion mas las variables observadas."""

    indice: float
    factores: dict[str, float]
    variables: dict

    def factor(self, codigo: str) -> float | None:
        return self.factores.get(codigo)

    def numero(self, variable: str, defecto: float = 0.0) -> float:
        valor = self.variables.get(variable)
        try:
            return float(valor)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return defecto

    def promedio(self, variables: list[str]) -> float | None:
        presentes = [
            float(self.variables[v])
            for v in variables
            if isinstance(self.variables.get(v), (int, float))
        ]
        return sum(presentes) / len(presentes) if presentes else None


@dataclass(frozen=True)
class Alerta:
    tipo: str
    severidad: str
    titulo: str
    detalle: str


class ReglaDeAlerta(Especificacion[ContextoDeAlerta]):
    """Especificacion que, si se satisface, produce una alerta."""

    tipo: str = "sin_tipo"
    titulo: str = ""

    @abstractmethod
    def es_satisfecha_por(self, c: ContextoDeAlerta) -> bool: ...

    @abstractmethod
    def construir(self, c: ContextoDeAlerta) -> Alerta: ...

    def evaluar(self, c: ContextoDeAlerta) -> Alerta | None:
        return self.construir(c) if self.es_satisfecha_por(c) else None


# --------------------------------------------------------------------------


class TrampaDeSuperacion(ReglaDeAlerta):
    codigo = tipo = "trampa_superacion"
    titulo = "Trampa de la superacion academica"
    descripcion = "Alta Efectividad con baja Superacion: el techo de rendimiento reduce el margen medible."

    def __init__(self, umbral_efectividad: float = 55.0, umbral_superacion: float = 30.0) -> None:
        self.umbral_efectividad = umbral_efectividad
        self.umbral_superacion = umbral_superacion

    def es_satisfecha_por(self, c: ContextoDeAlerta) -> bool:
        efectividad, superacion = c.factor("EFECTIVR"), c.factor("SUPERAR")
        if efectividad is None or superacion is None:
            return False
        return efectividad > self.umbral_efectividad and superacion < self.umbral_superacion

    def construir(self, c: ContextoDeAlerta) -> Alerta:
        return Alerta(
            tipo=self.tipo,
            severidad="alta",
            titulo=self.titulo,
            detalle=(
                f"Efectividad de {c.factor('EFECTIVR'):.1f} con Superacion de "
                f"{c.factor('SUPERAR'):.1f}. Un techo de rendimiento reduce el margen de avance "
                "medible, que pesa 28 % del indice."
            ),
        )


class RiesgoNormativo(ReglaDeAlerta):
    codigo = tipo = "riesgo_normativo"
    titulo = "Riesgo normativo por procesos sancionatorios"
    descripcion = "Procesos con sancion o multa que impactan Igualdad (22 %) y Mejoramiento (2 %)."

    def __init__(self, umbral_medio: float = 3.0, umbral_alto: float = 6.0) -> None:
        self.umbral_medio = umbral_medio
        self.umbral_alto = umbral_alto

    def _total(self, c: ContextoDeAlerta) -> float:
        return c.numero("procesos_con_sancion") + c.numero("procesos_multa")

    def es_satisfecha_por(self, c: ContextoDeAlerta) -> bool:
        return self._total(c) >= self.umbral_medio

    def construir(self, c: ContextoDeAlerta) -> Alerta:
        return Alerta(
            tipo=self.tipo,
            severidad="alta" if self._total(c) >= self.umbral_alto else "media",
            titulo=self.titulo,
            detalle=(
                f"{int(c.numero('procesos_con_sancion'))} procesos con sancion y "
                f"{int(c.numero('procesos_multa'))} con multa registrados. "
                "Impactan los factores Igualdad (22 %) y Mejoramiento (2 %)."
            ),
        )


class CaidaIdps(ReglaDeAlerta):
    codigo = tipo = "caida_idps"
    titulo = "Deterioro de indicadores de desarrollo personal y social"
    descripcion = "Promedio IDPS bajo el umbral; alimenta Iniciativa (6 %) e Integracion (5 %)."

    DIMENSIONES = ["idps_am_4b", "idps_cc_4b", "idps_pf_4b", "idps_hv_4b"]

    def __init__(self, umbral: float = 70.0) -> None:
        self.umbral = umbral

    def es_satisfecha_por(self, c: ContextoDeAlerta) -> bool:
        promedio = c.promedio(self.DIMENSIONES)
        return promedio is not None and promedio < self.umbral

    def construir(self, c: ContextoDeAlerta) -> Alerta:
        promedio = c.promedio(self.DIMENSIONES) or 0.0
        return Alerta(
            tipo=self.tipo,
            severidad="media",
            titulo=self.titulo,
            detalle=(
                f"Promedio IDPS de {promedio:.1f} puntos, bajo el umbral de {self.umbral:.0f}. "
                "Alimenta Iniciativa (6 %) e Integracion (5 %)."
            ),
        )


class FactorAcotadoDominante(ReglaDeAlerta):
    """Nueva tipologia habilitada por el patron: advierte cuando el resultado
    depende sobre todo de factores que el modelo no puede estimar bien."""

    codigo = tipo = "incertidumbre_alta"
    titulo = "Estimacion dominada por factores acotados"
    descripcion = "La mayor parte del indice proviene de factores limitados por informacion no publica."

    ACOTADOS = {"SUPERAR", "IGUALDR", "INICIAR", "INTEGRAR", "MEJORAR"}

    def __init__(self, umbral_proporcion: float = 0.55) -> None:
        self.umbral_proporcion = umbral_proporcion

    def _proporcion(self, c: ContextoDeAlerta) -> float:
        from q2_modelamiento.catalogo import pesos

        p = pesos()
        total = sum(v * p.get(k, 0.0) for k, v in c.factores.items())
        if total <= 0:
            return 0.0
        acotado = sum(v * p.get(k, 0.0) for k, v in c.factores.items() if k in self.ACOTADOS)
        return acotado / total

    def es_satisfecha_por(self, c: ContextoDeAlerta) -> bool:
        return bool(c.factores) and self._proporcion(c) >= self.umbral_proporcion

    def construir(self, c: ContextoDeAlerta) -> Alerta:
        return Alerta(
            tipo=self.tipo,
            severidad="informativa",
            titulo=self.titulo,
            detalle=(
                f"El {self._proporcion(c):.0%} del indice estimado proviene de factores acotados "
                "por informacion que solo el organismo emisor posee. Interprete la cifra como "
                "orden de magnitud, no como valor puntual."
            ),
        )


SIN_ALERTAS = Alerta(
    tipo="sin_alertas",
    severidad="informativa",
    titulo="Sin alertas activas",
    detalle="Ninguna de las tipologias monitoreadas supera su umbral en este periodo.",
)

REGLAS_POR_DEFECTO: tuple[ReglaDeAlerta, ...] = (
    TrampaDeSuperacion(),
    RiesgoNormativo(),
    CaidaIdps(),
    FactorAcotadoDominante(),
)


def evaluar(contexto: ContextoDeAlerta, reglas: tuple[ReglaDeAlerta, ...] | None = None) -> list[Alerta]:
    activas = [
        alerta
        for regla in (reglas if reglas is not None else REGLAS_POR_DEFECTO)
        if (alerta := regla.evaluar(contexto)) is not None
    ]
    return activas or [SIN_ALERTAS]
