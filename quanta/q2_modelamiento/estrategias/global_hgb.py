"""Estrategia GLOBAL — estimador de referencia.

HistGradientBoosting unico sobre las 65 variables de entrada. Liberado de la
restriccion de trazabilidad, responde a la pregunta puramente predictiva:
cual es la mejor estimacion alcanzable del indice (R2 = 0,6372).

Seleccionado como modelo de produccion frente al MLP (estadisticamente
equivalente, p = 0,1194) por cuatro criterios ARQUITECTONICOS, no metricos:
compatibilidad con el explicador exacto de Shapley para arboles, serializacion
en archivo unico sin dependencia del marco de aprendizaje profundo en
despliegue, ausencia de requerimiento de escalamiento y de aceleracion por
hardware, y menor dispersion entre particiones (0,0027 frente a 0,0072).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from q2_modelamiento.contrato import EstrategiaPredictiva, Prediccion
from q2_modelamiento.registro_modelos import (
    cargar_artefacto,
    medianas_imputacion,
    metadatos_global,
)

CATEGORICAS = {"CLUSTER", "cod_depe2", "BIENIO_PREMIO", "ES_RURAL", "tiene_convenio_sep"}


class EstrategiaGlobal(EstrategiaPredictiva):
    nombre = "global"
    version = "1.0.0"
    soporta_explicabilidad = False
    soporta_desglose_por_factor = False

    def __init__(self) -> None:
        self._meta = metadatos_global()
        self._medianas = medianas_imputacion()
        self._modelo = None

    def valores_de_referencia(self) -> dict[str, float]:
        """Valor con que se imputa cada variable ausente.

        Lo publica para que quien construya un escenario pueda partir del mismo
        punto que usara la prediccion. Sin esto, propagar una variacion sobre una
        variable ausente introduciria un salto artificial.
        """
        return dict(self._medianas)

    @property
    def variables_requeridas(self) -> list[str]:
        return list(self._meta["features_entrada"])

    def _cargar(self):
        if self._modelo is None:
            self._modelo = cargar_artefacto(self._meta["archivo"])
        return self._modelo

    def _matriz(self, observacion: dict) -> pd.DataFrame:
        fila = {}
        for v in self.variables_requeridas:
            valor = observacion.get(v)
            if valor is None or (isinstance(valor, float) and np.isnan(valor)):
                valor = self._medianas.get(v, 0 if v in CATEGORICAS else np.nan)
            fila[v] = valor
        return pd.DataFrame([fila], columns=self.variables_requeridas)

    def predecir(self, observacion: dict) -> Prediccion:
        modelo = self._cargar()
        X = self._matriz(observacion)
        indice = float(np.clip(modelo.predict(X)[0], 0.0, 100.0))
        return Prediccion(
            indice=round(indice, 2),
            factores={},
            estrategia=self.nombre,
            version_modelo=self.version,
            incertidumbre_mae=self._meta["metricas"]["mae"],
        )
