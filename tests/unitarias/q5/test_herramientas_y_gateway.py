"""Herramientas del agente y traduccion de errores del gateway."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluacion"))

from dobles import (  # noqa: E402
    RBD_AJENO,
    RBD_DEPURADO,
    RBD_SIN_ARTEFACTO,
    TRAMO_100,
    ServicioFalso,
)
from q5_agente.errores import (  # noqa: E402
    EstablecimientoNoEncontrado,
    FueraDeJurisdiccion,
    ParametroInvalido,
    ServicioNoDisponible,
)
from q5_agente.herramientas.catalogo import construir_catalogo  # noqa: E402


@pytest.fixture
def catalogo():
    return construir_catalogo(ServicioFalso())


# --- diagnostico ------------------------------------------------------------


def test_el_diagnostico_compone_prediccion_alertas_y_posicion(catalogo):
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=TRAMO_100)
    assert resultado.exito
    assert set(resultado.datos) >= {"prediccion", "alertas", "posicion"}
    assert resultado.datos["prediccion"]["indice"] == 67.60


def test_el_diagnostico_expone_las_cifras_para_el_guardarrail(catalogo):
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=TRAMO_100)
    assert 67.60 in resultado.cifras
    assert 0.37 in resultado.cifras, "el peso del factor debe quedar disponible"


def test_la_posicion_ausente_no_invalida_el_diagnostico():
    """La posicion es complementaria: su falta se declara, no rompe la respuesta."""

    class SinRanking(ServicioFalso):
        def obtener(self, ruta, parametros=None):
            if ruta.endswith("/ranking"):
                raise ServicioNoDisponible("vista de ranking no materializada")
            return super().obtener(ruta, parametros)

    catalogo = construir_catalogo(SinRanking())
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=TRAMO_100)
    assert resultado.exito
    assert resultado.datos["posicion"] is None
    assert "no disponible" in resultado.datos["nota_posicion"]


# --- traduccion de condiciones del servicio ---------------------------------


def test_un_rbd_ajeno_devuelve_fallo_controlado_y_menciona_la_jurisdiccion(catalogo):
    """CTRL-04: el agente no elude el control de acceso, lo hereda."""
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=RBD_AJENO)
    assert not resultado.exito
    assert "jurisdiccion" in resultado.error
    assert resultado.cifras == set(), "un fallo no puede aportar cifras"


def test_un_rbd_depurado_devuelve_fallo_controlado(catalogo):
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=RBD_DEPURADO)
    assert not resultado.exito
    assert "sin registros" in resultado.error


def test_un_artefacto_ausente_devuelve_fallo_controlado(catalogo):
    resultado = catalogo["diagnostico_de_establecimiento"].ejecutar(rbd=RBD_SIN_ARTEFACTO)
    assert not resultado.exito
    assert "artefacto" in resultado.error


# --- explicabilidad ---------------------------------------------------------


def test_la_explicacion_devuelve_contribuciones_y_aditividad(catalogo):
    resultado = catalogo["explicacion_por_factor"].ejecutar(rbd=TRAMO_100, factor="SUPERACR")
    assert resultado.exito
    assert resultado.datos["aditividad_verificada"] is True
    assert resultado.datos["factor"] == "SUPERACR"
    assert len(resultado.datos["contribuciones"]) >= 3


def test_el_factor_llega_normalizado_a_mayusculas(catalogo):
    resultado = catalogo["explicacion_por_factor"].ejecutar(rbd=TRAMO_100, factor="superacr")
    assert resultado.datos["factor"] == "SUPERACR"


# --- escenario --------------------------------------------------------------


def test_el_escenario_sin_variables_no_llama_al_servicio(catalogo):
    resultado = catalogo["simulacion_de_escenario"].ejecutar(rbd=TRAMO_100, variables={})
    assert not resultado.exito
    assert "variables" in resultado.error


def test_el_escenario_valido_devuelve_un_indice(catalogo):
    resultado = catalogo["simulacion_de_escenario"].ejecutar(
        rbd=TRAMO_100, variables={"tasa_aprobacion": 98.0}
    )
    assert resultado.exito
    assert resultado.datos["resultado"]["indice"] > 0
    assert resultado.datos["escenario"] == {"tasa_aprobacion": 98.0}


def test_una_variable_prohibida_no_llega_al_servicio(catalogo):
    """El objetivo del modelo no puede moverse: G-01 corta antes del gateway."""
    with pytest.raises(ParametroInvalido):
        catalogo["simulacion_de_escenario"].ejecutar(rbd=TRAMO_100, variables={"indicer": 100})


def test_un_valor_fuera_de_rango_lo_rechaza_el_servicio(catalogo):
    resultado = catalogo["simulacion_de_escenario"].ejecutar(
        rbd=TRAMO_100, variables={"simce_mat_4b": 900}
    )
    assert not resultado.exito
    assert "rango" in resultado.error


# --- pertinencia del ruteo --------------------------------------------------


@pytest.mark.parametrize(
    ("consulta", "esperada"),
    [
        ("Que posicion tenemos en el grupo homogeneo", "diagnostico_de_establecimiento"),
        ("Por que se nos cae la superacion", "explicacion_por_factor"),
        ("Que pasaria si subo la tasa de aprobacion", "simulacion_de_escenario"),
    ],
)
def test_la_pertinencia_ordena_las_herramientas(catalogo, consulta, esperada):
    puntajes = {nombre: h.pertinencia(consulta) for nombre, h in catalogo.items()}
    assert max(puntajes, key=puntajes.get) == esperada


def test_las_condiciones_del_servicio_son_excepciones_distinguibles():
    """Cada codigo tiene su excepcion: el bucle no razona sobre numeros HTTP."""
    servicio = ServicioFalso()
    with pytest.raises(FueraDeJurisdiccion):
        servicio.obtener(f"/prediccion/{RBD_AJENO}")
    with pytest.raises(EstablecimientoNoEncontrado):
        servicio.obtener(f"/prediccion/{RBD_DEPURADO}")
    with pytest.raises(ServicioNoDisponible):
        servicio.obtener(f"/prediccion/{RBD_SIN_ARTEFACTO}")
