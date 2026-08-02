"""Patron Decorator (Gamma et al., 1994) sobre EstrategiaPredictiva.

"Adjunta responsabilidades adicionales a un objeto de forma dinamica; los
decoradores ofrecen una alternativa flexible a la herencia para extender la
funcionalidad."

Dos responsabilidades transversales que NO deben vivir dentro de las
estrategias, porque se duplicarian en cada arquitectura futura y mezclarian
'predecir' con otra cosa:

  * auditar cada inferencia emitida (CTRL-05)
  * memoizar resultados costosos (Shapley exacto se invoca repetidamente)

Se componen: EstrategiaConCache(EstrategiaAuditada(EstrategiaDesagregada())).
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any, Callable

from q2_modelamiento.contrato import (
    CurvaSensibilidad,
    EstrategiaPredictiva,
    ExplicacionLocal,
    Prediccion,
)

log = logging.getLogger("sned.inferencias")


class DecoradorDeEstrategia(EstrategiaPredictiva):
    """Base de los decoradores: delega todo por omision."""

    def __init__(self, envuelta: EstrategiaPredictiva) -> None:
        self._envuelta = envuelta

    @property
    def nombre(self) -> str:  # type: ignore[override]
        return self._envuelta.nombre

    @property
    def version(self) -> str:  # type: ignore[override]
        return self._envuelta.version

    @property
    def soporta_explicabilidad(self) -> bool:  # type: ignore[override]
        return self._envuelta.soporta_explicabilidad

    @property
    def soporta_desglose_por_factor(self) -> bool:  # type: ignore[override]
        return self._envuelta.soporta_desglose_por_factor

    @property
    def variables_requeridas(self) -> list[str]:
        return self._envuelta.variables_requeridas

    def predecir(self, observacion: dict) -> Prediccion:
        return self._envuelta.predecir(observacion)

    def explicar(self, observacion: dict, factor: str | None = None) -> ExplicacionLocal:
        return self._envuelta.explicar(observacion, factor)

    def simular(self, observacion, variable, rango=None, n_puntos=25) -> CurvaSensibilidad:
        return self._envuelta.simular(observacion, variable, rango, n_puntos)

    def describir(self) -> dict:
        interno = self._envuelta.describir()
        interno.setdefault("decoradores", []).append(type(self).__name__)
        return interno


class EstrategiaAuditada(DecoradorDeEstrategia):
    """CTRL-05: persiste cada inferencia emitida.

    El sumidero es inyectable: en desarrollo escribe al log; en produccion
    recibe un callable que inserta en modelos.inferencia (PostgreSQL).
    """

    def __init__(
        self,
        envuelta: EstrategiaPredictiva,
        sumidero: Callable[[dict], None] | None = None,
    ) -> None:
        super().__init__(envuelta)
        self._sumidero = sumidero or self._registrar_en_log
        self.inferencias_emitidas = 0

    @staticmethod
    def _registrar_en_log(evento: dict) -> None:
        log.info("inferencia %s", evento)

    def predecir(self, observacion: dict) -> Prediccion:
        resultado = self._envuelta.predecir(observacion)
        self.inferencias_emitidas += 1
        self._sumidero(
            {
                "tipo": "prediccion",
                "rbd": observacion.get("rbd"),
                "bienio": observacion.get("BIENIO_PREMIO"),
                "estrategia": resultado.estrategia,
                "version_modelo": resultado.version_modelo,
                "valor_estimado": resultado.indice,
                "factores": resultado.factores,
            }
        )
        return resultado

    def explicar(self, observacion: dict, factor: str | None = None) -> ExplicacionLocal:
        explicacion = self._envuelta.explicar(observacion, factor)
        self._sumidero(
            {
                "tipo": "explicacion",
                "rbd": observacion.get("rbd"),
                "factor": factor,
                "valor_base": explicacion.valor_base,
                "prediccion": explicacion.prediccion,
                "contribuciones": {
                    c.variable: c.contribucion for c in explicacion.contribuciones[:10]
                },
            }
        )
        return explicacion


class EstrategiaConCache(DecoradorDeEstrategia):
    """Memoiza por firma de observacion. El calculo de Shapley exacto es caro
    y el simulador lo invoca repetidamente sobre el mismo establecimiento."""

    def __init__(self, envuelta: EstrategiaPredictiva, capacidad: int = 256) -> None:
        super().__init__(envuelta)
        self._capacidad = capacidad
        self._cache: OrderedDict[Any, Any] = OrderedDict()
        self.aciertos = 0
        self.fallos = 0

    @staticmethod
    def _firma(observacion: dict, sufijo: str = "") -> tuple:
        relevantes = tuple(
            sorted(
                (k, v)
                for k, v in observacion.items()
                if isinstance(v, (int, float, str, bool)) or v is None
            )
        )
        return (sufijo, relevantes)

    def _memoizar(self, clave, producir):
        if clave in self._cache:
            self.aciertos += 1
            self._cache.move_to_end(clave)
            return self._cache[clave]
        self.fallos += 1
        valor = producir()
        self._cache[clave] = valor
        if len(self._cache) > self._capacidad:
            self._cache.popitem(last=False)
        return valor

    def predecir(self, observacion: dict) -> Prediccion:
        return self._memoizar(
            self._firma(observacion, "predecir"),
            lambda: self._envuelta.predecir(observacion),
        )

    def explicar(self, observacion: dict, factor: str | None = None) -> ExplicacionLocal:
        return self._memoizar(
            self._firma(observacion, f"explicar:{factor}"),
            lambda: self._envuelta.explicar(observacion, factor),
        )

    def limpiar(self) -> None:
        self._cache.clear()
        self.aciertos = self.fallos = 0
