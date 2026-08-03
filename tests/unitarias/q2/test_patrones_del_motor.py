"""Cuanto 2: Decorator, Builder, Virtual Proxy y Factory Method.

Cada prueba verifica la PROPIEDAD que justifica el patron, no su forma.
Extraido de tests/test_patrones.py al reestructurar por tipo y por cuanto.
"""

from __future__ import annotations

from pathlib import Path

import pytest



# ---------------------------------------------------------------------------
# P5 · Decorator
# ---------------------------------------------------------------------------


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
# P8 · Builder
# ---------------------------------------------------------------------------


def test_builder_construye_escenario_inmutable_y_registra_los_cambios():
    from q2_modelamiento.escenario import ConstructorDeEscenario

    base = {"simce_mate_4b": 250.0, "tasa_aprobacion": 0.9}
    escenario = (
        ConstructorDeEscenario.desde(base)
        .con("simce_mate_4b", 280.0)
        .incrementar("tasa_aprobacion", 0.05)
        .construir()
    )

    assert escenario.variables["simce_mate_4b"] == 280.0
    assert round(escenario.variables["tasa_aprobacion"], 4) == 0.95
    assert base["simce_mate_4b"] == 250.0  # el original no se muta
    assert escenario.hay_cambios and "250.0 -> 280.0" in escenario.describir()


def test_builder_rechaza_variables_fuera_de_rango():
    from q2_modelamiento.escenario import ConstructorDeEscenario, VariableNoSimulable

    with pytest.raises(VariableNoSimulable):
        ConstructorDeEscenario.desde({"simce_mate_4b": 250.0}).con("simce_mate_4b", 900.0)


def test_builder_rechaza_variables_no_simulables():
    from q2_modelamiento.escenario import ConstructorDeEscenario, VariableNoSimulable

    constructor = ConstructorDeEscenario.desde({"a": 1}).con_variables_permitidas(["simce_mate_4b"])
    with pytest.raises(VariableNoSimulable):
        constructor.con("variable_inventada", 5.0)


def test_el_rango_valido_acota_la_malla_de_simulacion():
    from q2_modelamiento.escenario import ConstructorDeEscenario

    assert ConstructorDeEscenario.rango_valido("tasa_aprobacion") == (0.0, 1.0)
    assert ConstructorDeEscenario.rango_valido("simce_lect_4b") == (100.0, 400.0)
    assert ConstructorDeEscenario.rango_valido("n_docentes") is None


# ---------------------------------------------------------------------------
# P9 · Virtual Proxy
# ---------------------------------------------------------------------------


def test_el_proxy_no_toca_el_disco_hasta_el_primer_uso(tmp_path):
    from q2_modelamiento.artefactos import ArtefactoDiferido, ArtefactoNoDisponible

    proxy = ArtefactoDiferido(tmp_path / "no_existe.joblib")
    assert not proxy.materializado          # construirlo no falla ni carga
    with pytest.raises(ArtefactoNoDisponible):
        proxy.materializar()                 # el fallo llega al usarlo


def test_el_registro_entrega_proxies_sin_materializar(tmp_path):
    from q2_modelamiento.registro_modelos import RegistroDeModelos

    registro = RegistroDeModelos(carpeta_artefactos=tmp_path, carpeta_metadatos=tmp_path)
    artefacto = registro.obtener("modelo_X.joblib")
    assert not artefacto.materializado
    assert registro.obtener("modelo_X.joblib") is artefacto  # cacheado


# ---------------------------------------------------------------------------
# P6 · Factory Method
# ---------------------------------------------------------------------------


def test_la_fabrica_permite_registrar_arquitecturas_nuevas():
    from q2_modelamiento.fabrica import EstrategiaNoRegistrada, FabricaDeEstrategias

    fabrica = FabricaDeEstrategias()
    with pytest.raises(EstrategiaNoRegistrada):
        fabrica.crear("falsa")

    fabrica.registrar(_EstrategiaFalsa)  # type: ignore[arg-type]
    assert "falsa" in fabrica.disponibles()

    estrategia = fabrica.crear("falsa", auditar=False, cachear=False)
    assert estrategia.predecir({}).indice == 50.0


def test_la_fabrica_arma_la_cadena_de_decoradores():
    from q2_modelamiento.fabrica import FabricaDeEstrategias

    fabrica = FabricaDeEstrategias()
    fabrica.registrar(_EstrategiaFalsa)  # type: ignore[arg-type]

    decorada = fabrica.crear("falsa", auditar=True, cachear=True)
    decorada.predecir({"rbd": "1"})
    assert decorada.describir()["decoradores"] == ["EstrategiaAuditada", "EstrategiaConCache"]

