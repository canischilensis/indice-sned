"""Pruebas de los patrones de diseno aplicados.

Cada prueba verifica la PROPIEDAD que justifica el patron, no su forma:
que Specification compone, que Template Method impide omitir controles, que
Decorator no contamina, que Proxy difiere la carga, que Repository desacopla.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from compartido.especificacion import Especificacion, EspecificacionPredicado

# ---------------------------------------------------------------------------
# P4 · Specification
# ---------------------------------------------------------------------------


class _Mayor(Especificacion[int]):
    def __init__(self, n: int) -> None:
        self.n = n
        self.codigo = f"mayor_que_{n}"

    def es_satisfecha_por(self, c: int) -> bool:
        return c > self.n


class _Par(Especificacion[int]):
    codigo = "par"

    def es_satisfecha_por(self, c: int) -> bool:
        return c % 2 == 0


def test_specification_compone_con_y():
    spec = _Mayor(10).y(_Par())
    assert spec.es_satisfecha_por(12)
    assert not spec.es_satisfecha_por(11)
    assert not spec.es_satisfecha_por(4)


def test_specification_compone_con_o_y_no():
    assert _Mayor(10).o(_Par()).es_satisfecha_por(4)
    assert _Par().no().es_satisfecha_por(3)


def test_specification_admite_operadores():
    assert (_Mayor(10) & _Par()).es_satisfecha_por(12)
    assert (~_Par()).es_satisfecha_por(7)


def test_specification_conserva_trazabilidad_en_el_codigo():
    assert (_Mayor(5) & _Par()).codigo == "(mayor_que_5 Y par)"


def test_predicado_envuelve_funcion_existente():
    spec = EspecificacionPredicado("no_vacio", lambda s: bool(s))
    assert spec.es_satisfecha_por("x") and not spec.es_satisfecha_por("")


# ---------------------------------------------------------------------------
# P4 aplicado · reglas de cuarentena (CTRL-01)
# ---------------------------------------------------------------------------


def test_reglas_de_cuarentena_son_objetos_con_codigo():
    from q1_ingesta.reglas import REGLAS_BASE

    codigos = {r.codigo for r in REGLAS_BASE}
    assert codigos == {"rbd_ausente", "anio_ausente", "llave_duplicada"}
    assert all(r.descripcion for r in REGLAS_BASE)


def test_regla_de_ventana_temporal_es_componible():
    from q1_ingesta.calidad import aplicar_cuarentena
    from q1_ingesta.reglas import REGLAS_BASE, DentroDeVentanaTemporal

    df = pd.DataFrame(
        {
            "rbd": pd.array(["1", "2"], dtype="string"),
            "anio": [2024, 2024],
            "fecha": ["2024-03-01", "2025-12-31"],
        }
    )
    reglas = (*REGLAS_BASE, DentroDeVentanaTemporal("fecha", "2024-12-31"))
    validas, reporte = aplicar_cuarentena(df, "prueba", reglas=reglas, persistir=False)

    assert len(validas) == 1
    assert reporte.motivos == {"fuera_de_ventana": 1}
    assert "fuera_de_ventana" in reporte.reglas_aplicadas


def test_el_motivo_registrado_es_el_codigo_de_la_regla():
    from q1_ingesta.calidad import aplicar_cuarentena

    df = pd.DataFrame({"rbd": pd.array(["1", None, "1"], dtype="string"), "anio": [2024, 2024, 2024]})
    _, reporte = aplicar_cuarentena(df, "prueba", persistir=False)
    assert reporte.motivos == {"rbd_ausente": 1, "llave_duplicada": 1}


# ---------------------------------------------------------------------------
# P3 · Template Method
# ---------------------------------------------------------------------------


def test_template_method_aplica_los_controles_aunque_la_subclase_no_los_invoque(tmp_path):
    """La garantia del patron: una subclase no puede saltarse CTRL-01."""
    from q1_ingesta.fuentes import Fuente
    from q1_ingesta.ingestor import IngestorDeFuente

    fuente = Fuente("demo", "Demo", "org", "demo", "*.csv", ("rbd", "anio"), "anual")

    class IngestorDescuidado(IngestorDeFuente):
        """Solo implementa la lectura. No valida nada."""

        def _leer_archivo(self, ruta: Path) -> pd.DataFrame:
            return pd.DataFrame(
                {"RBD": pd.array(["0845", None, "0845"], dtype="string"), "anio": [2024, 2024, 2024]}
            )

        def _localizar(self):
            return [tmp_path / "falso.csv"]

    validas, reporte = IngestorDescuidado(fuente).ejecutar(persistir=False)

    assert reporte.filas_leidas == 3
    assert reporte.filas_cuarentena == 2          # nulo + duplicado, aislados sin pedirlo
    assert validas["rbd"].tolist() == ["845"]     # ceros a la izquierda normalizados


def test_template_method_falla_si_no_hay_archivos():
    from q1_ingesta.fuentes import Fuente
    from q1_ingesta.ingestor import IngestorCsv

    fuente = Fuente("inexistente", "X", "org", "no_existe", "*.csv", ("rbd",), "anual")
    with pytest.raises(FileNotFoundError):
        IngestorCsv(fuente).ejecutar(persistir=False)


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
