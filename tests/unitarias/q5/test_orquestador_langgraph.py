"""El segundo adaptador del puerto cumple el mismo contrato que el primero.

Estas pruebas no comparan calidad —eso lo hace `tests/evaluacion/comparar.py`
sobre los veinte casos—: verifican que el adaptador de LangGraph respeta las
mismas obligaciones del puerto, porque una comparacion entre dos cosas que no
cumplen lo mismo no compara nada.

Se omiten enteras si LangGraph no esta instalado. Es una dependencia opcional y
la suite debe correr en una maquina que no la tenga.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("langgraph", reason="dependencia opcional del orquestador alternativo")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluacion"))

from dobles import RBD_AJENO, RBDS_MUESTRA, ServicioFalso  # noqa: E402

from q5_agente.contrato import AsesorDeGestion, Consulta  # noqa: E402
from q5_agente.guardarrailes import PoliticaDeSalida, SanitizadorDeParametros  # noqa: E402
from q5_agente.herramientas.catalogo import construir_catalogo  # noqa: E402
from q5_agente.orquestadores.langgraph_react import AgenteLangGraph  # noqa: E402
from q5_agente.proveedores.determinista import AdaptadorDeterminista  # noqa: E402

pytestmark = pytest.mark.agente

RBD = RBDS_MUESTRA[0]


def _agente(servicio: ServicioFalso | None = None) -> AgenteLangGraph:
    servicio = servicio or ServicioFalso()
    herramientas = construir_catalogo(servicio, SanitizadorDeParametros())
    proveedor = AdaptadorDeterminista({h.nombre: h.disparadores for h in herramientas.values()})
    return AgenteLangGraph(proveedor, herramientas, PoliticaDeSalida(), max_pasos=3)


def test_implementa_el_puerto():
    assert isinstance(_agente(), AsesorDeGestion)
    assert AgenteLangGraph.nombre == "langgraph_react"


def test_responde_citando_solo_cifras_de_herramienta():
    respuesta = _agente().asesorar(Consulta(texto="Dame el diagnostico", rbd=RBD))

    assert respuesta.texto.strip()
    assert not respuesta.rechazada
    assert respuesta.llamadas, "sin llamada a herramienta no hay cifra que citar"
    assert respuesta.guardarrailes_aplicados == ["G-01", "G-02", "G-03"]


def test_la_traza_registra_lo_que_consulto():
    """La traza viaja hasta la pantalla: si no se registra aqui, no se ve alla."""
    respuesta = _agente().asesorar(Consulta(texto="Dame el diagnostico", rbd=RBD))

    llamada = respuesta.llamadas[0]
    assert llamada.herramienta == "diagnostico_de_establecimiento"
    assert llamada.exito
    assert llamada.resumen
    assert llamada.parametros["rbd"] == RBD


def test_el_rbd_de_la_sesion_manda_sobre_el_del_texto():
    """Misma regla que el bucle propio, y no es cosmetica: es CTRL-04.

    Si el orquestador dejara pasar el identificador que el modelo leyo en el
    texto, una consulta alcanzaria un establecimiento fuera de la jurisdiccion
    del usuario por el simple hecho de nombrarlo.
    """
    respuesta = _agente().asesorar(
        Consulta(texto=f"Dame el diagnostico del RBD: {RBD_AJENO}", rbd=RBD)
    )

    assert all(ll.parametros["rbd"] == RBD for ll in respuesta.llamadas)


def test_rechaza_una_promesa_de_retorno():
    """G-03 se aplica igual: la politica de salida es compartida, no reimplementada."""
    respuesta = _agente().asesorar(
        Consulta(texto="Me garantizas que ganamos la subvencion", rbd=RBD)
    )

    assert "no puedo comprometer" in respuesta.texto.lower()
    assert not respuesta.llamadas, "una consulta rechazada por politica no consulta datos"


def test_el_texto_llega_como_prosa_plana():
    respuesta = _agente().asesorar(Consulta(texto="Dame el diagnostico", rbd=RBD))

    assert "**" not in respuesta.texto
    assert "###" not in respuesta.texto


def test_contabiliza_tokens_y_llamadas_al_modelo():
    """Sin esta contabilidad la comparacion mide si aprueban, no lo que cuesta."""
    respuesta = _agente().asesorar(Consulta(texto="Dame el diagnostico", rbd=RBD))

    assert respuesta.uso.llamadas_al_modelo >= 1
    assert respuesta.uso.tokens_entrada > 0
    assert respuesta.uso.costo_usd == 0.0, "el determinista no cobra"


def test_describir_declara_el_orquestador_que_usa():
    descripcion = _agente().describir()

    assert descripcion["asesor"] == "langgraph_react"
    assert "create_react_agent" in descripcion["orquestador"]
