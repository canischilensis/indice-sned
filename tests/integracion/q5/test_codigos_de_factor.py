"""Los codigos de factor del cuanto 5 son los del motor, no una copia a ojo.

Existe por un defecto que la evaluacion no podia detectar. El catalogo del
agente declaraba SUPERACR, INICIATR, MEJORAMR e IGUALDAR; el motor los llama
SUPERAR, INICIAR, MEJORAR e IGUALDR. El modelo de lenguaje pedia con el codigo
declarado —hizo lo correcto— y el servicio respondia "Factor desconocido".

Los veinte casos criticos no lo vieron porque el doble del servicio replicaba la
constante equivocada en vez de la realidad. Un doble que refleja la
implementacion en lugar del sistema real bendice sus propios errores.

Esta prueba vive en tests/integracion y no dentro del cuanto: puede importar los
dos lados justamente porque no es parte de ninguno.
"""

from __future__ import annotations

from q2_modelamiento.validacion import COLUMNAS_OBJETIVO
from q5_agente.herramientas.catalogo import FACTORES

#: COLUMNAS_OBJETIVO incluye ademas el indice y el indicador socioeconomico, que
#: no son factores y que G-01 prohibe expresamente como parametro.
_NO_SON_FACTORES = {"SEL", "INDICER"}


def _factores_del_motor() -> set[str]:
    return set(COLUMNAS_OBJETIVO) - _NO_SON_FACTORES


def test_el_catalogo_declara_exactamente_los_factores_del_motor():
    declarados, reales = set(FACTORES), _factores_del_motor()
    assert declarados == reales, (
        f"sobran en el agente: {sorted(declarados - reales)}; "
        f"faltan: {sorted(reales - declarados)}"
    )


def test_son_seis_y_no_se_repiten():
    assert len(FACTORES) == len(set(FACTORES)) == 6


def test_el_objetivo_no_se_cuela_como_factor():
    """CTRL-02: el indice y el SEL no son palancas ni factores explicables."""
    assert _NO_SON_FACTORES.isdisjoint(FACTORES)
