"""QA-A: pruebas sobre los datos (CTRL-01)."""

import pandas as pd
import pytest

from q1_ingesta.calidad import ReporteCalidad, aplicar_cuarentena, normalizar_rbd

pytestmark = pytest.mark.datos


def test_rbd_conserva_ceros_a_la_izquierda_como_texto():
    serie = pd.Series(["00845", "9012"], dtype="string")
    assert normalizar_rbd(serie).tolist() == ["845", "9012"]


def test_registros_sin_llave_van_a_cuarentena_no_se_eliminan():
    df = pd.DataFrame({"rbd": pd.array(["845", None, "9012"], dtype="string"), "anio": [2024, 2024, 2024]})
    validas, reporte = aplicar_cuarentena(df, fuente="prueba")
    assert len(validas) == 2
    assert reporte.filas_cuarentena == 1
    assert reporte.filas_leidas == len(validas) + reporte.filas_cuarentena


def test_llave_duplicada_se_aisla():
    df = pd.DataFrame({"rbd": pd.array(["845", "845"], dtype="string"), "anio": [2024, 2024]})
    validas, reporte = aplicar_cuarentena(df, fuente="prueba")
    assert len(validas) == 1
    assert reporte.motivos.get("llave_duplicada") == 1


def test_umbral_de_cobertura_de_llave():
    r = ReporteCalidad("x", filas_leidas=100, filas_validas=96)
    assert r.cumple_umbral(0.95)
    assert not ReporteCalidad("x", filas_leidas=100, filas_validas=80).cumple_umbral(0.95)
