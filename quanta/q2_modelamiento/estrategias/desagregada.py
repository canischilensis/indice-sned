"""Estrategia DESAGREGADA — motor del simulador.

Seis modelos independientes, uno por factor, cada uno restringido a las
variables que la normativa declara como su insumo. El indice se reconstruye
con la formula legal, cuyas ponderaciones son dato de catalogo.

Esta arquitectura preserva la trazabilidad completa
    variable manipulada -> factor afectado -> indice
que es el requisito funcional del simulador. Paga por ello 0,054 puntos de R2
frente al modelo global (0,583 vs 0,637): el precio medido de la explicabilidad.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from q2_modelamiento import catalogo
from q2_modelamiento.contrato import (
    ContribucionVariable,
    CurvaSensibilidad,
    EstrategiaPredictiva,
    ExplicacionLocal,
    Prediccion,
)
from q2_modelamiento.etiquetas import etiqueta_de
from q2_modelamiento.escenario import ConstructorDeEscenario
from q2_modelamiento.registro_modelos import (
    cargar_artefacto,
    medianas_imputacion,
    metadatos_factores,
)

RANGO_FACTOR = (0.0, 100.0)


class EstrategiaDesagregada(EstrategiaPredictiva):
    nombre = "desagregado"
    version = "1.0.0"
    soporta_explicabilidad = True
    soporta_desglose_por_factor = True

    def __init__(self) -> None:
        self._meta = metadatos_factores()
        self._medianas = medianas_imputacion()
        self._codigos = [c for c in self._meta if not c.startswith("_")]
        self._modelos: dict[str, object] = {}
        self._explicadores: dict[str, object] = {}
        catalogo.verificar_suma_pesos()

    # -- ciclo de vida -----------------------------------------------------

    def _modelo(self, codigo: str):
        if codigo not in self._modelos:
            self._modelos[codigo] = cargar_artefacto(f"modelo_{codigo}.joblib")
        return self._modelos[codigo]

    def _variables(self, codigo: str) -> list[str]:
        return list(self._meta[codigo]["features"])

    def valores_de_referencia(self) -> dict[str, float]:
        """Valor con que se imputa cada variable ausente.

        Lo publica para que quien construya un escenario pueda partir del mismo
        punto que usara la prediccion. Sin esto, propagar una variacion sobre una
        variable ausente introduciria un salto artificial.
        """
        return dict(self._medianas)

    @property
    def variables_requeridas(self) -> list[str]:
        vistas: list[str] = []
        for codigo in self._codigos:
            for v in self._variables(codigo):
                if v not in vistas:
                    vistas.append(v)
        return vistas

    # -- preparacion de entrada -------------------------------------------

    def _matriz(self, observacion: dict, codigo: str) -> pd.DataFrame:
        """Imputacion por mediana mas banderas de ausencia.

        La ausencia es informacion, no defecto: junto a cada variable imputada
        viaja `<variable>_ausente`, que le dice al modelo que ese valor fue
        rellenado. Los artefactos fueron entrenados con ese par y por eso el
        orden de columnas se toma de `feature_names_in_` del propio modelo, no
        de la lista de metadatos, que solo enumera las variables base.
        """
        variables = self._variables(codigo)
        fila: dict[str, float] = {}
        ausente: dict[str, float] = {}
        for v in variables:
            valor = observacion.get(v)
            falta = valor is None or (isinstance(valor, float) and np.isnan(valor))
            ausente[f"{v}_ausente"] = 1.0 if falta else 0.0
            fila[v] = float(self._medianas.get(v, 0.0) if falta else valor)

        completa = {**fila, **ausente}
        nombres = getattr(self._modelo(codigo), "feature_names_in_", None)
        esperadas = list(nombres) if nombres is not None else variables
        return pd.DataFrame([{c: completa.get(c, 0.0) for c in esperadas}], columns=esperadas)

    # -- inferencia --------------------------------------------------------

    def _predecir_factor(self, observacion: dict, codigo: str) -> float:
        X = self._matriz(observacion, codigo)
        crudo = float(self._modelo(codigo).predict(X)[0])
        return float(np.clip(crudo, *RANGO_FACTOR))

    def predecir(self, observacion: dict) -> Prediccion:
        factores = {c: self._predecir_factor(observacion, c) for c in self._codigos}
        indice = catalogo.reconstruir_indice(factores)
        return Prediccion(
            indice=round(indice, 2),
            factores={c: round(v, 2) for c, v in factores.items()},
            estrategia=self.nombre,
            version_modelo=self.version,
            incertidumbre_mae=self._meta.get("_INDICER", {}).get("mae"),
        )

    # -- explicabilidad (valores de Shapley) -------------------------------

    def _explicador(self, codigo: str):
        if codigo not in self._explicadores:
            import shap

            # TreeExplainer inspecciona el TIPO del modelo, de modo que no
            # acepta el proxy: hay que entregarle el artefacto materializado.
            # Es el precio de la carga diferida y se paga aqui, una sola vez.
            self._explicadores[codigo] = shap.TreeExplainer(self._modelo(codigo).materializar())
        return self._explicadores[codigo]

    def explicar(self, observacion: dict, factor: str | None = None) -> ExplicacionLocal:
        codigo = factor or "EFECTIVR"
        if codigo not in self._codigos:
            raise ValueError(f"Factor desconocido: {codigo}. Validos: {self._codigos}")

        X = self._matriz(observacion, codigo)
        explicador = self._explicador(codigo)
        valores = np.asarray(explicador.shap_values(X)).reshape(-1)
        base = float(np.ravel(explicador.expected_value)[0])
        prediccion = self._predecir_factor(observacion, codigo)

        contribuciones = [
            ContribucionVariable(
                variable=v,
                etiqueta=etiqueta_de(v),
                valor=float(X.iloc[0][v]),
                contribucion=round(float(valores[i]), 4),
            )
            for i, v in enumerate(self._variables(codigo))
        ]
        contribuciones.sort(key=lambda c: abs(c.contribucion), reverse=True)
        return ExplicacionLocal(
            prediccion=round(prediccion, 2),
            valor_base=round(base, 2),
            contribuciones=contribuciones,
        )

    # -- analisis contrafactual (curvas ICE) -------------------------------

    def _factor_de(self, variable: str) -> str:
        for codigo in self._codigos:
            if variable in self._variables(codigo):
                return codigo
        raise ValueError(f"La variable '{variable}' no alimenta ningun factor del indice.")

    def simular(
        self,
        observacion: dict,
        variable: str,
        rango: list[float] | None = None,
        n_puntos: int = 25,
    ) -> CurvaSensibilidad:
        codigo = self._factor_de(variable)
        base = dict(observacion)
        actual = base.get(variable)
        if actual is None:
            actual = self._medianas.get(variable, 0.0)
            # Se fija el punto de partida en la propia observacion. Sin esto, el
            # constructor no puede calcular el delta y la variacion asociada no
            # se arrastra: la curva quedaria con la palanca movida y su derivada
            # congelada, que es justamente el defecto que se corrige.
            base[variable] = float(actual)

        limites = ConstructorDeEscenario.rango_valido(variable)
        if rango is None:
            centro = float(actual)
            if limites is not None:
                minimo, maximo = limites
                amplitud = (maximo - minimo) * 0.35
                rango = [max(centro - amplitud, minimo), min(centro + amplitud, maximo)]
            else:
                amplitud = max(abs(centro) * 0.6, 40.0)
                rango = [max(centro - amplitud, 0.0), centro + amplitud]
        elif limites is not None:
            rango = [max(rango[0], limites[0]), min(rango[1], limites[1])]

        malla = np.linspace(rango[0], rango[1], n_puntos)
        indices = []
        for punto in malla:
            escenario = (
                ConstructorDeEscenario.desde(base)
                .con_variables_permitidas(self._variables(codigo))
                .con_referencias(self._medianas)
                .con(variable, float(punto))
                .construir()
            )
            indices.append(self.predecir(escenario.variables).indice)

        return CurvaSensibilidad(
            variable=variable,
            valores=[round(float(v), 2) for v in malla],
            predicciones=[round(float(v), 3) for v in indices],
            valor_actual=round(float(actual), 2),
            prediccion_actual=self.predecir(base).indice,
        )
