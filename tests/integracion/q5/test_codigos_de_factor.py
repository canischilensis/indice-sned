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

from typing import Any

import pytest
from q2_modelamiento.validacion import COLUMNAS_OBJETIVO
from q5_agente.herramientas.catalogo import FACTORES, construir_catalogo
from q5_agente.proveedores.contrato import Mensaje
from q5_agente.proveedores.determinista import AdaptadorDeterminista

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


# ---------------------------------------------------------------------------
# El proveedor determinista
#
# La prueba de arriba comparaba dos copias de los codigos: la del motor y la del
# catalogo. Habia una tercera, en el mapa de ruteo del adaptador determinista, y
# nadie la miraba: por eso la suite quedaba en verde mientras la primera consulta
# real pedia SUPERACR y el servicio la rechazaba.
#
# Una duplicacion aceptada por ADR necesita una prueba por copia, no una por el
# par. Estas pruebas cubren la tercera ejecutando el adaptador por su interfaz
# publica, no leyendo su tabla: si manana el ruteo cambia de forma, siguen
# valiendo.
# ---------------------------------------------------------------------------

#: Una consulta por factor, redactada como la escribiria un directivo. Incluyen
#: "explica" y "factor" para que el ruteo elija la herramienta de explicacion y
#: la prueba mida el codigo, que es lo que esta bajo examen.
_CONSULTA_POR_FACTOR = {
    "EFECTIVR": "explica el factor de efectividad",
    "SUPERAR": "explica el factor de superacion",
    "IGUALDR": "explica el factor de igualdad de oportunidades",
    "INICIAR": "explica el factor de iniciativa",
    "INTEGRAR": "explica el factor de integracion y participacion",
    "MEJORAR": "explica el factor de mejoramiento de condiciones",
}


class _PuertaInerte:
    """Cumple el protocolo PuertaDeServicio y falla si alguien la usa.

    Estas pruebas solo leen esquemas y ruteo; ninguna ejecuta una herramienta.
    Si una llegara a hacerlo, es un cambio de alcance y debe verse.
    """

    def obtener(self, ruta: str, parametros: dict[str, Any] | None = None) -> dict:
        raise AssertionError(f"el ruteo no debe llamar al servicio: GET {ruta}")

    def enviar(self, ruta: str, cuerpo: dict[str, Any]) -> dict:
        raise AssertionError(f"el ruteo no debe llamar al servicio: POST {ruta}")


def _rutear(consulta: str):
    """Ejecuta el adaptador determinista como lo hace el bucle, y devuelve la peticion."""
    herramientas = construir_catalogo(_PuertaInerte())
    descriptores = [
        {"nombre": h.nombre, "descripcion": h.descripcion, "esquema": h.esquema()}
        for h in herramientas.values()
    ]
    proveedor = AdaptadorDeterminista({h.nombre: h.disparadores for h in herramientas.values()})
    return proveedor.completar([Mensaje("usuario", consulta)], descriptores).peticion


@pytest.mark.parametrize("codigo,consulta", sorted(_CONSULTA_POR_FACTOR.items()))
def test_el_determinista_rutea_cada_factor_a_su_codigo(codigo: str, consulta: str):
    peticion = _rutear(consulta)
    assert peticion is not None, f"'{consulta}' no produjo peticion de herramienta"
    assert peticion.nombre == "explicacion_por_factor"
    assert peticion.parametros.get("factor") == codigo


def test_el_determinista_no_emite_ningun_codigo_ajeno_al_catalogo():
    """La regresion concreta: SUPERACR, IGUALDAR, INICIATR y MEJORAMR no existen."""
    emitidos = {_rutear(c).parametros.get("factor") for c in _CONSULTA_POR_FACTOR.values()}
    ajenos = sorted(emitidos - set(FACTORES))
    assert not ajenos, f"codigos fuera del catalogo: {ajenos}"


def test_las_consultas_de_prueba_cubren_los_seis_factores():
    """Si el catalogo suma o retira un factor, esta prueba lo exige aqui tambien."""
    assert set(_CONSULTA_POR_FACTOR) == set(FACTORES)


@pytest.mark.parametrize(
    "consulta",
    [
        "explica por que nos fue asi este ano",
        "por que la contribucion cambio tanto",
        "explica la causa de lo que esta pasando",
    ],
)
def test_sin_factor_reconocible_responde_el_diagnostico_general(consulta: str):
    """No se adivina un factor: se responde sobre los seis.

    Antes, una consulta sin factor identificable devolvia el primer codigo
    admitido y terminaba explicando Efectividad sin decirlo. El diagnostico
    general nombra los seis con su aporte y su restriccion, de modo que responde
    la pregunta sin elegir por el usuario.
    """
    peticion = _rutear(consulta)
    assert peticion is not None
    assert peticion.nombre == "diagnostico_de_establecimiento"
    assert "factor" not in peticion.parametros


def test_ningun_ruteo_pide_explicacion_sin_factor():
    """La herramienta admite `factor` opcional; el ruteo no debe apoyarse en eso.

    Pedir la explicacion sin factor devolveria el predeterminado del servicio, y
    seria el mismo silencio con otra forma.
    """
    consultas = [*_CONSULTA_POR_FACTOR.values(), "explica por que nos fue asi este ano"]
    for consulta in consultas:
        peticion = _rutear(consulta)
        if peticion.nombre == "explicacion_por_factor":
            assert peticion.parametros.get("factor"), f"'{consulta}' pide explicacion sin factor"
