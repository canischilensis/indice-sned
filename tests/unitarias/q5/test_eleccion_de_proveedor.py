"""AGENTE_PROVEEDOR y AGENTE_MODELO son dos variables, y se confunden.

Nace de un tropiezo real de uso: al cambiar de modelo se escribio el nombre del
modelo en AGENTE_PROVEEDOR. El mensaje "Proveedor 'gemini-3.6-flash' desconocido.
Disponibles: anthropic, determinista, gemini, openai" era cierto y completamente
inutil: enumeraba lo correcto sin nombrar el error que la persona tenia delante.

Un mensaje de configuracion tiene que decir que escribir, no solo que esta mal.
"""

from __future__ import annotations

import pytest
from q5_agente.config import ConfiguracionDelAgente
from q5_agente.errores import ProveedorNoConfigurado
from q5_agente.fabrica import crear_proveedor


def _con(proveedor: str) -> ConfiguracionDelAgente:
    return ConfiguracionDelAgente().con(agente_proveedor=proveedor)


@pytest.mark.parametrize(
    ("modelo", "proveedor"),
    [
        ("gemini-3.6-flash", "gemini"),
        ("gemini-2.0-flash", "gemini"),
        ("gemma-4-31b-it", "gemini"),
        ("claude-sonnet-4-5", "anthropic"),
        ("gpt-4.1", "openai"),
    ],
)
def test_un_modelo_escrito_como_proveedor_se_nombra_como_tal(modelo, proveedor):
    with pytest.raises(ProveedorNoConfigurado) as excepcion:
        crear_proveedor(_con(modelo))

    mensaje = str(excepcion.value)
    assert "es un MODELO, no un proveedor" in mensaje
    assert f"AGENTE_PROVEEDOR={proveedor}" in mensaje, "debe decir que escribir"
    assert f"AGENTE_MODELO={modelo}" in mensaje


def test_un_proveedor_inventado_sigue_dando_el_mensaje_llano():
    """Sin prefijo reconocible no se adivina nada: solo se enumera lo que hay."""
    with pytest.raises(ProveedorNoConfigurado) as excepcion:
        crear_proveedor(_con("llama-local"))

    mensaje = str(excepcion.value)
    assert "desconocido" in mensaje
    assert "es un MODELO" not in mensaje
    assert "determinista" in mensaje


def test_el_proveedor_valido_no_se_toca():
    proveedor = crear_proveedor(_con("determinista"))
    assert proveedor.nombre == "determinista"
