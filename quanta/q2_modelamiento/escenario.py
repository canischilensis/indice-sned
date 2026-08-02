"""Patron Builder (Gamma et al., 1994) — construccion de escenarios contrafactuales.

"Separa la construccion de un objeto complejo de su representacion, de modo que
el mismo proceso de construccion pueda crear representaciones distintas."

La fuerza: el simulador debe permitir mover varias palancas a la vez (meta
declarada: >= 4 factores simulables) y validar que cada variable exista y caiga
en rango. Construir escenarios con `dict(base); base[v] = x` disperso por tres
modulos no escala ni valida nada.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class VariableNoSimulable(ValueError):
    """La variable no alimenta ningun factor del indice."""


@dataclass(frozen=True)
class Escenario:
    """Objeto de valor inmutable: una observacion con cambios declarados."""

    variables: dict[str, float | str | None]
    cambios: dict[str, tuple[float | None, float]] = field(default_factory=dict)

    @property
    def hay_cambios(self) -> bool:
        return bool(self.cambios)

    def describir(self) -> str:
        if not self.cambios:
            return "Escenario base, sin modificaciones."
        partes = [
            f"{v}: {'—' if antes is None else round(antes, 2)} -> {round(despues, 2)}"
            for v, (antes, despues) in self.cambios.items()
        ]
        return "; ".join(partes)


class ConstructorDeEscenario:
    """Interfaz fluida para armar un escenario validado.

        escenario = (ConstructorDeEscenario.desde(observacion)
                     .con_variables_permitidas(motor.variables_requeridas)
                     .con("simce_mate_4b", 290)
                     .incrementar("tasa_aprobacion", 0.03)
                     .construir())
    """

    RANGOS = {
        "simce": (100.0, 400.0),
        "idps": (0.0, 100.0),
        "tasa": (0.0, 1.0),
    }

    def __init__(self, base: dict) -> None:
        self._base = dict(base)
        self._cambios: dict[str, tuple[float | None, float]] = {}
        self._permitidas: set[str] | None = None

    @classmethod
    def desde(cls, observacion: dict) -> ConstructorDeEscenario:
        return cls(observacion)

    @classmethod
    def rango_valido(cls, variable: str) -> tuple[float, float] | None:
        """Rango admisible de la variable, o None si no esta acotada.

        Lo consulta el simulador para que la malla de la curva ICE nunca
        proponga valores que el propio constructor rechazaria.
        """
        for prefijo, limites in cls.RANGOS.items():
            if variable.startswith(prefijo) or f"_{prefijo}" in variable:
                return limites
        return None

    def con_variables_permitidas(self, variables) -> ConstructorDeEscenario:
        self._permitidas = set(variables)
        return self

    # -- operaciones -------------------------------------------------------

    def con(self, variable: str, valor: float) -> ConstructorDeEscenario:
        self._validar(variable, valor)
        anterior = self._base.get(variable)
        self._cambios[variable] = (
            float(anterior) if isinstance(anterior, (int, float)) else None,
            float(valor),
        )
        self._base[variable] = float(valor)
        return self

    def incrementar(self, variable: str, delta: float) -> ConstructorDeEscenario:
        actual = self._base.get(variable)
        if not isinstance(actual, (int, float)):
            raise VariableNoSimulable(
                f"'{variable}' no tiene valor numerico de partida; usa .con() con un valor absoluto."
            )
        return self.con(variable, float(actual) + float(delta))

    def en_porcentaje(self, variable: str, porcentaje: float) -> ConstructorDeEscenario:
        actual = self._base.get(variable)
        if not isinstance(actual, (int, float)):
            raise VariableNoSimulable(f"'{variable}' no tiene valor numerico de partida.")
        return self.con(variable, float(actual) * (1.0 + porcentaje / 100.0))

    def construir(self) -> Escenario:
        return Escenario(variables=dict(self._base), cambios=dict(self._cambios))

    # -- validacion --------------------------------------------------------

    def _validar(self, variable: str, valor: float) -> None:
        if self._permitidas is not None and variable not in self._permitidas:
            raise VariableNoSimulable(
                f"'{variable}' no alimenta ningun factor del indice y por tanto no es simulable."
            )
        try:
            numero = float(valor)
        except (TypeError, ValueError) as exc:
            raise VariableNoSimulable(f"'{variable}' requiere un valor numerico.") from exc

        for prefijo, (minimo, maximo) in self.RANGOS.items():
            if variable.startswith(prefijo) or f"_{prefijo}" in variable:
                if not (minimo <= numero <= maximo):
                    raise VariableNoSimulable(
                        f"'{variable}' = {numero} cae fuera del rango valido [{minimo}, {maximo}]."
                    )
                return
