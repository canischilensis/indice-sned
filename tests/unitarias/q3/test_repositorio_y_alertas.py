"""Cuanto 3: Repository con adaptadores intercambiables y reglas de alerta.

Cada prueba verifica la PROPIEDAD que justifica el patron, no su forma.
Extraido de tests/test_patrones.py al reestructurar por tipo y por cuanto.
"""

from __future__ import annotations

import pytest


class _EstrategiaFalsa:
    """Doble de prueba: no carga artefactos."""

    nombre = "falsa"
    version = "0.0.1"
    soporta_explicabilidad = True
    soporta_desglose_por_factor = True

    def __init__(self) -> None:
        self.llamadas = 0

    @property
    def variables_requeridas(self):
        return ["simce_mate_4b"]

    def predecir(self, observacion):
        from q2_modelamiento.contrato import Prediccion

        self.llamadas += 1
        return Prediccion(indice=50.0, factores={"EFECTIVR": 50.0}, estrategia="falsa", version_modelo="0.0.1")

    def explicar(self, observacion, factor=None):
        raise NotImplementedError

    def simular(self, observacion, variable, rango=None, n_puntos=25):
        raise NotImplementedError

    def describir(self):
        return {"nombre": self.nombre}


def test_decorador_de_auditoria_registra_sin_tocar_la_estrategia():
    from q2_modelamiento.decoradores import EstrategiaAuditada

    eventos = []
    interna = _EstrategiaFalsa()
    auditada = EstrategiaAuditada(interna, sumidero=eventos.append)

    auditada.predecir({"rbd": "845"})

    assert auditada.inferencias_emitidas == 1
    assert eventos[0]["rbd"] == "845" and eventos[0]["valor_estimado"] == 50.0
    assert interna.llamadas == 1  # la estrategia no sabe que fue auditada


def test_decorador_de_cache_evita_recalcular():
    from q2_modelamiento.decoradores import EstrategiaConCache

    interna = _EstrategiaFalsa()
    cacheada = EstrategiaConCache(interna)

    for _ in range(3):
        cacheada.predecir({"rbd": "845", "simce_mate_4b": 250.0})

    assert interna.llamadas == 1
    assert cacheada.aciertos == 2 and cacheada.fallos == 1


def test_los_decoradores_se_componen_y_se_declaran():
    from q2_modelamiento.decoradores import EstrategiaAuditada, EstrategiaConCache

    compuesta = EstrategiaConCache(EstrategiaAuditada(_EstrategiaFalsa()))
    compuesta.predecir({"rbd": "845"})

    descripcion = compuesta.describir()
    assert descripcion["decoradores"] == ["EstrategiaAuditada", "EstrategiaConCache"]
    assert compuesta.nombre == "falsa"  # la identidad se preserva




# ---------------------------------------------------------------------------
# P2 · Repository
# ---------------------------------------------------------------------------


class _RepositorioFalso:
    origen = "memoria"

    def __init__(self, datos: dict) -> None:
        self._datos = datos

    def obtener(self, rbd, periodo=None):
        from q3_servicio.repositorios import EstablecimientoNoEncontrado

        if rbd not in self._datos:
            raise EstablecimientoNoEncontrado(rbd)
        return dict(self._datos[rbd])

    def listar(self, rbds, limite=50):
        return [{"rbd": r} for r in rbds if r in self._datos]

    def existe(self, rbd):
        return rbd in self._datos

    def describir(self):
        return {"origen": self.origen}


def test_el_servicio_funciona_contra_cualquier_adaptador():
    """La propiedad que justifica Repository: el servicio no sabe de dónde viene el dato."""
    from q3_servicio.servicios.motor import ServicioDePrediccion

    servicio = ServicioDePrediccion(
        estrategia=_EstrategiaFalsa(),  # type: ignore[arg-type]
        repositorio=_RepositorioFalso({"845": {"simce_mate_4b": 250.0}}),  # type: ignore[arg-type]
    )
    variables = servicio.variables_de("845")
    respuesta = servicio.predecir("845", variables)

    assert respuesta.indice == 50.0
    assert servicio.describir()["repositorio"]["origen"] == "memoria"


def test_los_dos_adaptadores_cumplen_el_mismo_contrato():
    from q3_servicio.repositorios import (
        RepositorioEstablecimientos,
        RepositorioParquet,
        RepositorioPostgres,
    )

    for clase in (RepositorioParquet, RepositorioPostgres):
        assert issubclass(clase, RepositorioEstablecimientos)
        assert not getattr(clase, "__abstractmethods__", None)


# ---------------------------------------------------------------------------
# Reglas de alerta como especificaciones
# ---------------------------------------------------------------------------


def test_todas_las_reglas_de_alerta_se_evaluan_no_solo_la_primera():
    """No es una cadena de responsabilidad: no hay corte tras el primer acierto."""
    from q3_servicio.servicios.reglas_alerta import ContextoDeAlerta, evaluar

    contexto = ContextoDeAlerta(
        indice=48.0,
        factores={"EFECTIVR": 70.0, "SUPERAR": 10.0},
        variables={"procesos_con_sancion": 5, "procesos_multa": 3, "idps_cc_4b": 50.0},
    )
    tipos = {a.tipo for a in evaluar(contexto)}
    assert {"trampa_superacion", "riesgo_normativo", "caida_idps"} <= tipos


def test_sin_condiciones_activas_se_devuelve_la_alerta_informativa():
    from q3_servicio.servicios.reglas_alerta import ContextoDeAlerta, evaluar

    contexto = ContextoDeAlerta(indice=50.0, factores={}, variables={})
    alertas = evaluar(contexto)
    assert len(alertas) == 1 and alertas[0].tipo == "sin_alertas"


def test_los_umbrales_de_una_regla_son_parametrizables():
    from q3_servicio.servicios.reglas_alerta import ContextoDeAlerta, RiesgoNormativo

    contexto = ContextoDeAlerta(indice=50.0, factores={}, variables={"procesos_con_sancion": 2})
    assert not RiesgoNormativo().es_satisfecha_por(contexto)
    assert RiesgoNormativo(umbral_medio=1).es_satisfecha_por(contexto)
