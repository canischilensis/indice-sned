"""Los veinte casos criticos, ejecutados como parte de la suite."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from arnes import construir_agente, evaluar_caso  # noqa: E402
from casos import CASOS  # noqa: E402
from dobles import ServicioFalso  # noqa: E402

pytestmark = pytest.mark.agente


@pytest.mark.parametrize("caso", CASOS, ids=[c.id for c in CASOS])
def test_caso_critico(caso):
    servicio = ServicioFalso()
    agente = construir_agente(servicio)
    resultado = evaluar_caso(caso, agente, servicio)
    assert resultado.aprobado, f"{caso.id}: " + " | ".join(resultado.fallos)


def test_ninguna_respuesta_cita_cifras_sin_respaldo():
    """G-02 agregado sobre los veinte casos: es la metrica que no admite excepcion."""
    huerfanas = {}
    for caso in CASOS:
        servicio = ServicioFalso()
        resultado = evaluar_caso(caso, construir_agente(servicio), servicio)
        if resultado.cifras_sin_respaldo:
            huerfanas[caso.id] = resultado.cifras_sin_respaldo
    assert not huerfanas, f"Cifras sin respaldo por caso: {huerfanas}"


def test_ninguna_respuesta_promete_retorno():
    """G-03 agregado. El beneficio se asigna por posicion relativa."""
    promesas = {}
    for caso in CASOS:
        servicio = ServicioFalso()
        resultado = evaluar_caso(caso, construir_agente(servicio), servicio)
        if resultado.promesas_detectadas:
            promesas[caso.id] = resultado.promesas_detectadas
    assert not promesas, f"Promesas de retorno por caso: {promesas}"
