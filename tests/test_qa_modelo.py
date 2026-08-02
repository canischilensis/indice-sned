"""QA-B: pruebas sobre el modelo y el catalogo (CTRL-02)."""

import numpy as np
import pandas as pd
import pytest

from q2_modelamiento import catalogo
from q2_modelamiento.validacion import (
    FugaDeDatos,
    predictor_trivial,
    verificar_exclusion_objetivo,
    verificar_particion_limpia,
)

pytestmark = pytest.mark.modelo


def test_ponderaciones_del_catalogo_suman_uno():
    catalogo.verificar_suma_pesos()
    assert abs(sum(catalogo.pesos().values()) - 1.0) < 1e-9


def test_formula_oficial_reconstruye_el_indice():
    valores = {c: 50.0 for c in catalogo.pesos()}
    assert abs(catalogo.reconstruir_indice(valores) - 50.0) < 1e-9


def test_reconstruccion_falla_si_falta_un_factor():
    with pytest.raises(ValueError):
        catalogo.reconstruir_indice({"EFECTIVR": 50.0})


def test_variable_objetivo_entre_predictores_bloquea_el_entrenamiento():
    with pytest.raises(FugaDeDatos):
        verificar_exclusion_objetivo(["simce_mate_4b", "SUPERAR"], objetivo="EFECTIVR")


def test_particion_con_establecimiento_compartido_es_fuga():
    df = pd.DataFrame({"rbd": ["1", "1", "2", "3"]})
    with pytest.raises(FugaDeDatos):
        verificar_particion_limpia(df, idx_train=[0, 2], idx_test=[1, 3])


def test_predictor_trivial_devuelve_la_media():
    y = np.array([1.0, 3.0, 5.0])
    assert np.allclose(predictor_trivial(y, 2), [3.0, 3.0])


def test_frontera_de_informacion_declarada():
    acotados = [f for f in catalogo.factores().values() if f.es_acotado]
    assert len(acotados) == 5
    assert abs(sum(f.peso for f in acotados) - 0.63) < 0.01
