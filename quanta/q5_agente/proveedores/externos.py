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

#: Gemini nombra "model" lo que las otras dos APIs llaman "assistant", y no
#: admite un rol de sistema dentro de la conversacion: va en `system_instruction`.
_ROL_GEMINI = {
    "usuario": "user",
    "herramienta": "user",
    "asistente": "model",
}


def _a_esquema_de_funcion(herramienta: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": herramienta["nombre"],
        "description": herramienta["descripcion"],
        "input_schema": herramienta["esquema"],
    }


# --- traduccion de esquema para Gemini ------------------------------------
#
# Gemini no acepta JSON Schema completo, sino un subconjunto de OpenAPI 3.0.
# `additionalProperties` no forma parte de ese subconjunto, y la herramienta
# `simulacion_de_escenario` lo usa para declarar el mapa variable -> valor.
# Traducir es responsabilidad del adaptador: el catalogo no se deforma para
# acomodar a un proveedor, que es justamente lo que el puerto evita.

_CLAVES_ADMITIDAS = frozenset(
    {"type", "description", "enum", "items", "properties", "required", "nullable", "format"}
)


def _a_esquema_gemini(nodo: Any) -> Any:
    """Poda el esquema a las claves del subconjunto OpenAPI que Gemini admite.

    Lo unico que se pierde es la restriccion de tipo sobre los valores de un
    mapa abierto. El sanitizador G-01 ya la impone del lado del agente, que es
    donde debe imponerse: un guardarrail no puede depender de que el proveedor
    respete el esquema.
    """
    if isinstance(nodo, list):
        return [_a_esquema_gemini(x) for x in nodo]
    if not isinstance(nodo, dict):
        return nodo

    podado: dict[str, Any] = {}
    for clave, valor in nodo.items():
        if clave not in _CLAVES_ADMITIDAS:
            continue
        if clave == "properties" and isinstance(valor, dict):
            # Las claves de `properties` son nombres de parametro, no palabras
            # del esquema: se conservan todas y se poda solo su contenido.
            podado[clave] = {nombre: _a_esquema_gemini(sub) for nombre, sub in valor.items()}
        elif clave in {"enum", "required"}:
            podado[clave] = list(valor) if isinstance(valor, (list, tuple)) else valor
        else:
            podado[clave] = _a_esquema_gemini(valor)

    extra = nodo.get("additionalProperties")
    if isinstance(extra, dict) and "properties" not in podado:
        tipo = extra.get("type", "valor")
        base = podado.get("description", "")
        podado["description"] = (
            f"{base} Mapa abierto: las claves son nombres de variable y los valores son de "
            f"tipo {tipo}."
        ).strip()
    return podado


def _a_declaracion_gemini(herramienta: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": herramienta["nombre"],
        "description": herramienta["descripcion"],
        "parameters": _a_esquema_gemini(herramienta["esquema"]),
    }


def _es_modelo_inexistente(error: Exception) -> bool:
    """404 sobre el nombre del modelo: es configuracion, no una caida.

    La distincion importa porque el cortacircuitos (G-04) existe para proteger
    al sistema de un proveedor que se cayo, y reintentar contra un modelo que no
    existe nunca va a funcionar. Tratarlo como fallo del proveedor haria que
    tres consultas mal configuradas abrieran el circuito y ocultaran la causa
    real tras un mensaje de indisponibilidad.
    """
    texto = str(error).lower()
    return "404" in texto and ("not_found" in texto or "not found" in texto)


def _es_rechazo_de_muestreo(error: Exception) -> bool:
    """El modelo rechaza temperature/top_p/top_k, en deprecacion en la linea 3.x."""
    texto = str(error).lower()
    parametro = any(p in texto for p in ("temperature", "top_p", "top_k"))
    return parametro and any(
        s in texto for s in ("invalid", "unsupported", "not supported", "400", "deprecat")
    )


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


class AdaptadorGemini(ProveedorDeModelo):
    """Adaptador para la API de Gemini (SDK `google-genai`).

    Cuatro diferencias con los otros dos adaptadores, todas resueltas aqui
    dentro para que el bucle no se entere:

    1. El mensaje de sistema no viaja en la conversacion sino en
       `system_instruction`.
    2. El esquema de las funciones es un subconjunto de OpenAPI, no JSON Schema.
    3. Los **tokens de razonamiento** se facturan como salida y llegan en un
       contador aparte. Sumarlos no es opcional: omitirlos haria que la
       instrumentacion de costo declare menos de lo que el proyecto gasta.
    4. La familia de modelos **rota**, y con ella los parametros admitidos. Un
       modelo retirado responde 404 y los parametros de muestreo estan en
       deprecacion en la linea 3.x. Las dos condiciones se distinguen de una
       caida real del proveedor, porque reintentar no las arregla.
    """

    nombre = "gemini"

    #: Precio por millon de tokens, por modelo (nivel de pago estandar,
    #: agosto de 2026). El precio depende del modelo, de modo que fijarlo como
    #: constante de clase haria mentir a la instrumentacion en cuanto alguien
    #: cambiara AGENTE_MODELO.
    #:
    #: Los 2.5 se conservan porque siguen facturandose a quien ya los usaba,
    #: pero Google los cerro a claves nuevas: si su clave es reciente,
    #: respondera 404 aunque el precio figure aqui.
    PRECIOS: dict[str, tuple[float, float]] = {
        "gemini-2.5-flash-lite": (0.10, 0.40),
        "gemini-2.5-flash": (0.30, 2.50),
        "gemini-2.5-pro": (1.25, 10.00),
        "gemini-3.1-flash-lite": (0.25, 1.50),
        "gemini-3.5-flash-lite": (0.30, 2.50),
        "gemini-3.5-flash": (1.50, 9.00),
        "gemini-3.6-flash": (1.50, 7.50),
        "gemini-3.1-pro-preview": (2.00, 12.00),
    }

    #: Recomendado por Google para claves nuevas. El defecto anterior
    #: —gemini-2.5-flash— fue un error: sigue documentado y con precio
    #: publicado, pero cerrado a usuarios nuevos.
    MODELO_PREDETERMINADO = "gemini-3.6-flash"

    def __init__(self, modelo: str = MODELO_PREDETERMINADO, clave: str | None = None) -> None:
        try:
            from google import genai  # noqa: PLC0415
            from google.genai import types  # noqa: PLC0415
        except ImportError as exc:
            raise ProveedorNoConfigurado(
                "El paquete 'google-genai' no esta instalado. Instalelo con "
                "'pip install google-genai' o use el proveedor determinista."
            ) from exc

        api_key = clave or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProveedorNoConfigurado(
                "Falta la variable de entorno GEMINI_API_KEY. La clave se emite en Google AI "
                "Studio; una suscripcion de consumidor a Gemini no habilita la API."
            )

        self._tipos = types
        self._cliente = genai.Client(api_key=api_key)
        self._modelo = modelo

        precio = self.PRECIOS.get(modelo)
        #: Falso cuando el modelo no esta en la tabla: el costo se reporta como
        #: cero y `describir()` lo declara, en vez de inventar una tarifa.
        self.precio_declarado = precio is not None
        self.usd_por_millon_entrada, self.usd_por_millon_salida = precio or (0.0, 0.0)

        #: Se apaga solo, y para siempre, si el modelo rechaza el muestreo.
        self._con_muestreo = True

    def modelos_disponibles(self) -> list[str]:
        """Modelos que esta clave puede usar. Sirve para elegir AGENTE_MODELO.

        La familia rota mas rapido que la documentacion: un modelo con precio
        publicado puede estar cerrado a claves nuevas. Preguntarle a la clave es
        la unica respuesta que no envejece.
        """
        try:
            return sorted(
                m.name.removeprefix("models/")
                for m in self._cliente.models.list()
                if getattr(m, "name", None)
            )
        except Exception as exc:  # noqa: BLE001
            raise ErrorDelProveedor(f"No se pudo listar los modelos: {exc}") from exc

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        tipos = self._tipos
        instruccion = "\n\n".join(m.contenido for m in mensajes if m.rol == "sistema")
        contenidos = [
            tipos.Content(
                role=_ROL_GEMINI.get(m.rol, "user"),
                parts=[tipos.Part(text=m.contenido)],
            )
            for m in mensajes
            if m.rol != "sistema"
        ]
        herramienta_unica = tipos.Tool(
            function_declarations=[_a_declaracion_gemini(h) for h in herramientas]
        )

        def config(con_muestreo: bool) -> Any:
            comunes: dict[str, Any] = {
                "system_instruction": instruccion or None,
                "tools": [herramienta_unica],
            }
            # temperature=0 es lo que hace repetible una evaluacion. Se pide
            # mientras el modelo lo acepte; la linea 3.x lo esta deprecando.
            if con_muestreo:
                comunes["temperature"] = 0
            return tipos.GenerateContentConfig(**comunes)

        try:
            respuesta = self._cliente.models.generate_content(
                model=self._modelo, contents=contenidos, config=config(self._con_muestreo)
            )
        except Exception as exc:  # noqa: BLE001 - la SDK expone jerarquias propias
            if self._con_muestreo and _es_rechazo_de_muestreo(exc):
                # No es una caida: es un parametro que este modelo ya no admite.
                # Se reintenta una vez sin el y se recuerda, para no volver a
                # gastar una llamada en lo mismo.
                self._con_muestreo = False
                return self.completar(mensajes, herramientas)
            if _es_modelo_inexistente(exc):
                raise ProveedorNoConfigurado(
                    f"El modelo '{self._modelo}' no esta disponible para esta clave. "
                    "Liste los modelos de su clave y fije AGENTE_MODELO con uno de "
                    f"ellos. Detalle del proveedor: {exc}"
                ) from exc
            raise ErrorDelProveedor(f"Fallo la llamada al proveedor: {exc}") from exc

        entrada, salida = self._contar(respuesta)
        partes = self._partes(respuesta)

        for parte in partes:
            llamada = getattr(parte, "function_call", None)
            if llamada is not None and getattr(llamada, "name", None):
                return RespuestaDelModelo(
                    peticion=PeticionDeHerramienta(llamada.name, dict(llamada.args or {})),
                    tokens_entrada=entrada,
                    tokens_salida=salida,
                )

        texto = "".join(getattr(p, "text", "") or "" for p in partes)
        return RespuestaDelModelo(texto=texto, tokens_entrada=entrada, tokens_salida=salida)

    @staticmethod
    def _partes(respuesta: Any) -> list[Any]:
        """Extrae las partes sin usar `.text`, que revienta si solo hubo llamada."""
        candidatos = getattr(respuesta, "candidates", None) or []
        if not candidatos:
            return []
        contenido = getattr(candidatos[0], "content", None)
        return list(getattr(contenido, "parts", None) or [])

    @staticmethod
    def _contar(respuesta: Any) -> tuple[int, int]:
        """Tokens de entrada y de salida, con el razonamiento contado como salida."""
        uso = getattr(respuesta, "usage_metadata", None)
        entrada = getattr(uso, "prompt_token_count", 0) or 0
        salida = getattr(uso, "candidates_token_count", 0) or 0
        razonamiento = getattr(uso, "thoughts_token_count", 0) or 0
        return entrada, salida + razonamiento

    def describir(self) -> dict[str, Any]:
        return {
            "proveedor": self.nombre,
            "modelo": self._modelo,
            "precio_declarado": self.precio_declarado,
        }
