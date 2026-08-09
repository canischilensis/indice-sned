"""Adaptadores de proveedores externos.

Un adaptador por proveedor, todos detras del mismo puerto. La importacion del
paquete es perezosa y esta contenida: si el paquete no esta instalado o falta la
credencial, el adaptador falla con ProveedorNoConfigurado en su construccion y
no al medio de una consulta.

Ninguno de estos adaptadores calcula nada del indice. Reciben el catalogo de
herramientas y devuelven, o una peticion de herramienta, o texto.
"""

from __future__ import annotations

import json
import os
from typing import Any

from q5_agente.errores import ErrorDelProveedor, ProveedorNoConfigurado
from q5_agente.proveedores.contrato import (
    Mensaje,
    PeticionDeHerramienta,
    ProveedorDeModelo,
    RespuestaDelModelo,
)

_ROL_HTTP = {
    "sistema": "system",
    "usuario": "user",
    "asistente": "assistant",
    "herramienta": "user",
}


def _a_esquema_de_funcion(herramienta: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": herramienta["nombre"],
        "description": herramienta["descripcion"],
        "input_schema": herramienta["esquema"],
    }


class AdaptadorAnthropic(ProveedorDeModelo):
    """Adaptador para la API de mensajes de Anthropic."""

    nombre = "anthropic"
    usd_por_millon_entrada = 3.0
    usd_por_millon_salida = 15.0

    def __init__(self, modelo: str = "claude-sonnet-4-5", clave: str | None = None) -> None:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:
            raise ProveedorNoConfigurado(
                "El paquete 'anthropic' no esta instalado. Instalelo o use el proveedor "
                "determinista."
            ) from exc
        api_key = clave or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProveedorNoConfigurado("Falta la variable de entorno ANTHROPIC_API_KEY.")
        self._cliente = anthropic.Anthropic(api_key=api_key)
        self._modelo = modelo

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        sistema = "\n\n".join(m.contenido for m in mensajes if m.rol == "sistema")
        conversacion = [
            {"role": _ROL_HTTP.get(m.rol, "user"), "content": m.contenido}
            for m in mensajes
            if m.rol != "sistema"
        ]
        try:
            respuesta = self._cliente.messages.create(
                model=self._modelo,
                max_tokens=1200,
                temperature=0,
                system=sistema,
                tools=[_a_esquema_de_funcion(h) for h in herramientas],
                messages=conversacion,
            )
        except Exception as exc:  # noqa: BLE001 - la SDK expone jerarquias propias
            raise ErrorDelProveedor(f"Fallo la llamada al proveedor: {exc}") from exc

        uso = getattr(respuesta, "usage", None)
        entrada = getattr(uso, "input_tokens", 0) or 0
        salida = getattr(uso, "output_tokens", 0) or 0

        for bloque in respuesta.content:
            if getattr(bloque, "type", "") == "tool_use":
                return RespuestaDelModelo(
                    peticion=PeticionDeHerramienta(bloque.name, dict(bloque.input or {})),
                    tokens_entrada=entrada,
                    tokens_salida=salida,
                )
        texto = "".join(
            getattr(b, "text", "") for b in respuesta.content if getattr(b, "type", "") == "text"
        )
        return RespuestaDelModelo(texto=texto, tokens_entrada=entrada, tokens_salida=salida)


class AdaptadorOpenAI(ProveedorDeModelo):
    """Adaptador para la API de completado de OpenAI."""

    nombre = "openai"
    usd_por_millon_entrada = 2.5
    usd_por_millon_salida = 10.0

    def __init__(self, modelo: str = "gpt-4.1", clave: str | None = None) -> None:
        try:
            from openai import OpenAI  # noqa: PLC0415
        except ImportError as exc:
            raise ProveedorNoConfigurado(
                "El paquete 'openai' no esta instalado. Instalelo o use el proveedor determinista."
            ) from exc
        api_key = clave or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProveedorNoConfigurado("Falta la variable de entorno OPENAI_API_KEY.")
        self._cliente = OpenAI(api_key=api_key)
        self._modelo = modelo

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        conversacion = [
            {"role": _ROL_HTTP.get(m.rol, "user"), "content": m.contenido} for m in mensajes
        ]
        funciones = [
            {
                "type": "function",
                "function": {
                    "name": h["nombre"],
                    "description": h["descripcion"],
                    "parameters": h["esquema"],
                },
            }
            for h in herramientas
        ]
        try:
            respuesta = self._cliente.chat.completions.create(
                model=self._modelo, temperature=0, messages=conversacion, tools=funciones
            )
        except Exception as exc:  # noqa: BLE001
            raise ErrorDelProveedor(f"Fallo la llamada al proveedor: {exc}") from exc

        uso = getattr(respuesta, "usage", None)
        entrada = getattr(uso, "prompt_tokens", 0) or 0
        salida = getattr(uso, "completion_tokens", 0) or 0
        eleccion = respuesta.choices[0].message

        if getattr(eleccion, "tool_calls", None):
            llamada = eleccion.tool_calls[0]
            try:
                parametros = json.loads(llamada.function.arguments or "{}")
            except json.JSONDecodeError:
                parametros = {}
            return RespuestaDelModelo(
                peticion=PeticionDeHerramienta(llamada.function.name, parametros),
                tokens_entrada=entrada,
                tokens_salida=salida,
            )
        return RespuestaDelModelo(
            texto=eleccion.content or "", tokens_entrada=entrada, tokens_salida=salida
        )
