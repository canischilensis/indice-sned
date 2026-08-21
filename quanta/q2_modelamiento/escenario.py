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


#: Prefijo de las variables derivadas que deben seguir a su palanca.
#:
#: El modelo aprendio con ocho variables `dif_simce_*` —la variacion del puntaje
#: respecto del bienio anterior— que se calculan como `actual - previo`. El
#: bienio previo es un hecho consumado: no se puede simular. Por lo tanto, si el
#: directivo mueve `simce_mate_4b` en +10, `dif_simce_mate_4b` sube exactamente
#: +10, porque el sustraendo no cambia.
#:
#: Sin esta propagacion el simulador le entrega al modelo media senal: el puntaje
#: se mueve y la variacion queda congelada en su valor imputado. El indice
#: responde poco o de forma incoherente, que es exactamente el defecto observado.
_PREFIJO_DERIVADA = "dif_"


def derivada_de(variable: str) -> str | None:
    """Nombre de la variable derivada que acompana a esta palanca, si existe."""
    return f"{_PREFIJO_DERIVADA}{variable}" if variable.startswith("simce_") else None


@dataclass(frozen=True)
class Escenario:
    """Objeto de valor inmutable: una observacion con cambios declarados."""

    variables: dict[str, float | str | None]
    cambios: dict[str, tuple[float | None, float]] = field(default_factory=dict)
    #: Variables que el escenario movio por consecuencia, no por peticion. Viajan
    #: aparte de `cambios` porque el directivo no las pidio y tiene derecho a
    #: saber que se movieron: un cambio propagado en silencio es indistinguible
    #: de un modelo que responde solo.
    derivados: dict[str, tuple[float | None, float]] = field(default_factory=dict)

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
        texto = "; ".join(partes)
        if self.derivados:
            arrastradas = "; ".join(
                f"{v}: {'—' if antes is None else round(antes, 2)} -> {round(despues, 2)}"
                for v, (antes, despues) in self.derivados.items()
            )
            texto += f". Por consecuencia: {arrastradas}"
        return texto


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

    #: Una variacion no es un puntaje. `dif_simce_mate_4b` = +12 significa que
    #: el establecimiento subio doce puntos, y contra el rango absoluto de SIMCE
    #: —[100, 400]— seria rechazada por «fuera de rango». Se declara aparte y se
    #: consulta antes que RANGOS, porque el nombre contiene la cadena `simce` y
    #: la busqueda por subcadena la clasificaria mal.
    RANGO_DE_VARIACION = (-300.0, 300.0)

    def __init__(self, base: dict) -> None:
        self._base = dict(base)
        self._cambios: dict[str, tuple[float | None, float]] = {}
        self._derivados: dict[str, tuple[float | None, float]] = {}
        self._permitidas: set[str] | None = None
        self._referencias: dict[str, float] = {}

    @classmethod
    def desde(cls, observacion: dict) -> ConstructorDeEscenario:
        return cls(observacion)

    @classmethod
    def rango_valido(cls, variable: str) -> tuple[float, float] | None:
        """Rango admisible de la variable, o None si no esta acotada.

        Lo consulta el simulador para que la malla de la curva ICE nunca
        proponga valores que el propio constructor rechazaria.
        """
        if variable.startswith(_PREFIJO_DERIVADA):
            return cls.RANGO_DE_VARIACION
        for prefijo, limites in cls.RANGOS.items():
            if variable.startswith(prefijo) or f"_{prefijo}" in variable:
                return limites
        return None

    def con_variables_permitidas(self, variables) -> ConstructorDeEscenario:
        self._permitidas = set(variables)
        return self

    def con_referencias(self, valores: dict[str, float] | None) -> ConstructorDeEscenario:
        """Valor efectivo de las variables que la observacion no trae.

        Una variable ausente no vale cero al predecir: la estrategia la imputa
        por mediana antes de armar la matriz. Para propagar una variacion sobre
        ella hay que partir de ese mismo valor, o el escenario introduciria un
        salto que no corresponde a ninguna decision de gestion.
        """
        self._referencias = dict(valores or {})
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
        self._propagar_a_derivada(variable, anterior, float(valor))
        return self

    def _propagar_a_derivada(
        self, variable: str, anterior: object, nuevo: float
    ) -> None:
        """Arrastra la variacion asociada a la palanca que se acaba de mover.

        `dif_x = x_actual - x_previo`, y el bienio previo no es simulable. La
        consecuencia aritmetica es que la variacion se mueve exactamente el mismo
        delta que la palanca. No se estima: se deduce.

        Si no hay valor de partida numerico, no hay delta que propagar y la
        derivada queda como estaba. Se prefiere no mover nada antes que inventar
        un punto de partida.
        """
        derivada = derivada_de(variable)
        if derivada is None or not isinstance(anterior, (int, float)):
            return
        if self._permitidas is not None and derivada not in self._permitidas:
            return

        partida = self._base.get(derivada)
        if not isinstance(partida, (int, float)):
            partida = self._referencias.get(derivada)
        if not isinstance(partida, (int, float)):
            return

        delta = nuevo - float(anterior)
        minimo, maximo = self.RANGO_DE_VARIACION
        propagado = max(minimo, min(maximo, float(partida) + delta))
        self._base[derivada] = propagado
        self._derivados[derivada] = (float(partida), propagado)

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
        return Escenario(
            variables=dict(self._base),
            cambios=dict(self._cambios),
            derivados=dict(self._derivados),
        )

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
