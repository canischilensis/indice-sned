"""Patron Specification: el mecanismo componible (cuanto compartido).

Cada prueba verifica la PROPIEDAD que justifica el patron, no su forma.
Extraido de tests/test_patrones.py al reestructurar por tipo y por cuanto.
"""

from __future__ import annotations

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

