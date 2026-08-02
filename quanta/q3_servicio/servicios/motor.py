"""Fachada del motor predictivo para la capa HTTP (Facade, Gamma et al., 1994).

"Proporciona una interfaz unificada a un conjunto de interfaces de un
subsistema; define una interfaz de mas alto nivel que hace al subsistema mas
facil de usar."

Unico punto del cuanto 3 que dialoga con el cuanto 2. Recibe sus colaboradores
por constructor, de modo que las pruebas de aceptacion pueden inyectar un motor
falso y ejercitar la API completa sin cargar 220 MB de artefactos.
"""

from __future__ import annotations

from q2_modelamiento import ConstructorDeEscenario, EstrategiaPredictiva, obtener_estrategia
from q2_modelamiento.catalogo import factores as catalogo_factores
from q2_modelamiento.etiquetas import etiqueta_de
from q3_servicio.esquemas.predictivo import (
    Alerta as AlertaSalida,
)
from q3_servicio.esquemas.predictivo import (
    ContribucionSalida,
    FactorPredicho,
    RespuestaExplicacion,
    RespuestaPrediccion,
    RespuestaSimulacion,
)
from q3_servicio.repositorios import RepositorioEstablecimientos, RepositorioParquet
from q3_servicio.servicios import reglas_alerta
from q3_servicio.servicios.reglas_alerta import ContextoDeAlerta, ReglaDeAlerta

ADVERTENCIA_DECISION = (
    "Estimacion con incertidumbre cuantificada. La IA asiste; la decision "
    "estrategica y financiera la toma exclusivamente el equipo directivo."
)

ADVERTENCIA_ESCALAMIENTO = (
    "El indice normaliza cada factor contra los extremos nacionales: el resultado "
    "depende del desempeno del conjunto del sistema. Una mejora realista de 15 a 20 "
    "puntos SIMCE aporta del orden de 0,5 puntos al indice. La curva comunica "
    "direccion y sensibilidad, no una promesa de retorno."
)


class ServicioDePrediccion:
    """Fachada. Sus tres colaboradores se inyectan por constructor."""

    def __init__(
        self,
        estrategia: EstrategiaPredictiva | None = None,
        repositorio: RepositorioEstablecimientos | None = None,
        reglas: tuple[ReglaDeAlerta, ...] | None = None,
    ) -> None:
        self._estrategia = estrategia or obtener_estrategia()
        self._repositorio = repositorio or RepositorioParquet()
        self._reglas = reglas if reglas is not None else reglas_alerta.REGLAS_POR_DEFECTO

    # -- acceso a datos ----------------------------------------------------

    def variables_de(self, rbd: str, periodo: str | None = None, sobreescrituras: dict | None = None) -> dict:
        base = self._repositorio.obtener(rbd, periodo)
        if sobreescrituras:
            constructor = ConstructorDeEscenario.desde(base)
            for variable, valor in sobreescrituras.items():
                if valor is not None:
                    constructor = constructor.con(variable, valor)
            return constructor.construir().variables
        return base

    # -- casos de uso ------------------------------------------------------

    def predecir(self, rbd: str, variables: dict) -> RespuestaPrediccion:
        resultado = self._estrategia.predecir(variables)
        catalogo = catalogo_factores()

        detalle = [
            FactorPredicho(
                codigo=codigo,
                nombre=catalogo[codigo].nombre,
                peso=catalogo[codigo].peso,
                valor=valor,
                aporte_al_indice=round(valor * catalogo[codigo].peso, 2),
                es_acotado=catalogo[codigo].es_acotado,
                es_accionable=catalogo[codigo].es_accionable,
                restriccion=catalogo[codigo].restriccion,
            )
            for codigo, valor in resultado.factores.items()
        ]
        detalle.sort(key=lambda f: f.aporte_al_indice, reverse=True)

        return RespuestaPrediccion(
            rbd=rbd,
            indice=resultado.indice,
            factores=detalle,
            estrategia=resultado.estrategia,
            version_modelo=resultado.version_modelo,
            incertidumbre_mae=resultado.incertidumbre_mae,
            advertencia=ADVERTENCIA_DECISION,
        )

    def explicar(self, rbd: str, variables: dict, factor: str) -> RespuestaExplicacion:
        explicacion = self._estrategia.explicar(variables, factor=factor)

        contribuciones = [
            ContribucionSalida(
                variable=c.variable,
                etiqueta=c.etiqueta,
                valor=c.valor,
                contribucion=c.contribucion,
                direccion=c.direccion,
            )
            for c in explicacion.contribuciones
        ]
        lectura = "; ".join(
            f"{c.etiqueta} aporta {c.contribucion:+.2f}" for c in contribuciones[:3]
        ) or "Sin contribuciones relevantes."

        return RespuestaExplicacion(
            rbd=rbd,
            factor=factor,
            prediccion=explicacion.prediccion,
            valor_base=explicacion.valor_base,
            aditividad_verificada=explicacion.verificar_aditividad(tolerancia=0.5),
            contribuciones=contribuciones,
            lectura=lectura,
        )

    def simular(
        self, rbd: str, variables: dict, variable: str, rango: list[float] | None, n_puntos: int
    ) -> RespuestaSimulacion:
        curva = self._estrategia.simular(variables, variable=variable, rango=rango, n_puntos=n_puntos)
        return RespuestaSimulacion(
            rbd=rbd,
            variable=curva.variable,
            etiqueta=etiqueta_de(curva.variable),
            valores=curva.valores,
            predicciones=curva.predicciones,
            valor_actual=curva.valor_actual,
            prediccion_actual=curva.prediccion_actual,
            monotona=curva.es_monotona_creciente,
            advertencia_magnitud=ADVERTENCIA_ESCALAMIENTO,
        )

    def evaluar_alertas(self, prediccion: RespuestaPrediccion, variables: dict) -> list[AlertaSalida]:
        contexto = ContextoDeAlerta(
            indice=prediccion.indice,
            factores={f.codigo: f.valor for f in prediccion.factores},
            variables=variables,
        )
        return [
            AlertaSalida(tipo=a.tipo, severidad=a.severidad, titulo=a.titulo, detalle=a.detalle)
            for a in reglas_alerta.evaluar(contexto, self._reglas)
        ]

    def diagnostico_de_cobertura(self) -> dict:
        """Desajuste entre entrenamiento y servicio (training/serving skew).

        Las variables que el modelo espera y el conjunto servido no provee se
        imputan por mediana. Funciona, pero degrada la estimacion en silencio:
        este diagnostico lo vuelve observable en lugar de invisible.
        """
        requeridas = set(self._estrategia.variables_requeridas)
        disponibles = getattr(self._repositorio, "variables_disponibles", lambda: None)()
        if disponibles is None:
            return {"evaluable": False, "motivo": "El repositorio no declara sus columnas."}

        faltantes = sorted(requeridas - disponibles)
        return {
            "evaluable": True,
            "n_requeridas": len(requeridas),
            "n_disponibles": len(requeridas) - len(faltantes),
            "cobertura": round(1 - len(faltantes) / len(requeridas), 4) if requeridas else 1.0,
            "faltantes": faltantes,
            "efecto": (
                "Las variables faltantes se imputan por mediana; la estimacion se degrada "
                "de forma proporcional al peso de esas variables."
                if faltantes
                else "Cobertura completa."
            ),
        }

    def describir(self) -> dict:
        return {
            "estrategia": self._estrategia.describir(),
            "repositorio": self._repositorio.describir(),
            "reglas_de_alerta": [r.codigo for r in self._reglas],
            "cobertura_de_variables": self.diagnostico_de_cobertura(),
        }


# --- inyeccion de dependencias para FastAPI --------------------------------

_servicio: ServicioDePrediccion | None = None


def servicio_de_prediccion() -> ServicioDePrediccion:
    """Dependencia de FastAPI. Sobrescribible en pruebas con
    `app.dependency_overrides[servicio_de_prediccion] = lambda: doble`."""
    global _servicio
    if _servicio is None:
        _servicio = ServicioDePrediccion()
    return _servicio
