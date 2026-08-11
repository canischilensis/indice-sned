"""Adaptador para un modelo de lenguaje que corre en la maquina del usuario.

## Por que Ollama y no otro modelo alojado mas

Gemini, OpenAI y Anthropic son tres APIs alojadas de frontera. Entre ellas se
miden matices: cual redacta mejor, cual cuesta menos, cual rutea con menos
titubeos. Ollama no es un cuarto competidor en esa lista, **es otro eje**:

| | Alojado | Local |
|---|---|---|
| Costo por consulta | centavos | cero |
| El dato del establecimiento | sale del pais | no sale de la maquina |
| Disponibilidad | depende de un tercero | depende de quien opera |
| Calidad del ruteo | alta | **es lo que se va a medir** |

La tercera fila y la segunda son las que importan en este dominio. Son datos de
establecimientos identificados por RBD, de educacion publica chilena. Un asesor
que corre en la infraestructura del sostenedor, sin que el dato viaje a una API
extranjera, es un argumento de politica de datos y no una optimizacion de costo.

## Lo que este adaptador espera encontrar, y lo que espera NO encontrar

**Se espera peor ruteo, y eso no es un fallo.** Un modelo de siete u ocho mil
millones de parametros no elige herramienta como uno de frontera. Si de veinte
casos acierta doce, **doce es el resultado**: ajustar los casos hasta que apruebe
seria exactamente lo que el plan de calidad de este proyecto prohibe.

La pregunta que la tesis puede responder con numeros es cuanto se degrada el
ruteo de herramientas al bajar de un modelo de frontera a uno local, y esa
pregunta solo tiene valor si la respuesta puede ser incomoda.

## Ni un SDK

Los otros tres adaptadores importan el paquete de su proveedor. Este habla la API
nativa de Ollama, que es HTTP con JSON, de modo que **`httpx` alcanza** — lo que
el cuanto 5 ya tenia. Es el unico proveedor que no agrega una sola dependencia, y
en una comparacion donde se cuentan las dependencias transitivas, eso se nota.

## Sobre la latencia

Sin GPU, un modelo de esta talla tarda decenas de segundos por paso y el bucle da
dos o tres. La fila de latencia entonces **no compara dos modelos: compara una
maquina de escritorio contra un centro de datos**, y hay que escribirlo con esas
palabras o el numero miente.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from q5_agente.errores import ErrorDelProveedor, ProveedorNoConfigurado
from q5_agente.proveedores.contrato import (
    Mensaje,
    PeticionDeHerramienta,
    ProveedorDeModelo,
    RespuestaDelModelo,
)

#: Ollama distingue el rol `tool`, a diferencia de los adaptadores que traducen
#: la observacion como si fuera del usuario. Se aprovecha: el modelo recibe la
#: conversacion con la forma que su plantilla espera.
_ROL = {
    "sistema": "system",
    "usuario": "user",
    "asistente": "assistant",
    "herramienta": "tool",
}


class AdaptadorOllama(ProveedorDeModelo):
    """Modelo local servido por Ollama, por su API nativa."""

    nombre = "ollama"
    #: Corre en la maquina: no hay tarifa. El costo existe y es electrico y de
    #: tiempo, pero no es el que esta instrumentacion mide, y declararlo cero es
    #: mas honesto que inventar una equivalencia.
    usd_por_millon_entrada = 0.0
    usd_por_millon_salida = 0.0

    MODELO_PREDETERMINADO = "qwen3:8b"

    def __init__(
        self,
        modelo: str | None = None,
        url_base: str = "http://127.0.0.1:11434",
        segundos_espera: float = 180.0,
        cliente: httpx.Client | None = None,
    ) -> None:
        self._modelo = modelo or self.MODELO_PREDETERMINADO
        self._url = url_base.rstrip("/") + "/api/chat"
        # Tres minutos, no diez segundos como los proveedores alojados. En CPU un
        # paso puede tardar mas de un minuto, y un tiempo de espera corto
        # convertiria la lentitud esperada en un fallo del proveedor, que es una
        # conclusion distinta y equivocada.
        self._espera = segundos_espera
        # Cliente inyectable. Existe para poder probar la traduccion de la
        # respuesta sin levantar un servidor: verificar el adaptador contra un
        # Ollama real solo diria que Ollama funciona, no que la traduccion sea
        # correcta, y son dos cosas distintas.
        self._cliente = cliente

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        cuerpo: dict[str, Any] = {
            "model": self._modelo,
            "messages": [
                {"role": _ROL.get(m.rol, "user"), "content": m.contenido} for m in mensajes
            ],
            "stream": False,
        }
        if herramientas:
            cuerpo["tools"] = [
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
            respuesta = self._enviar(cuerpo)
        except httpx.ConnectError as exc:
            raise ProveedorNoConfigurado(
                f"No hay un servidor Ollama escuchando en {self._url}. "
                "Instalelo desde ollama.com y descargue el modelo con "
                f"'ollama pull {self._modelo}'."
            ) from exc
        except httpx.HTTPError as exc:
            raise ErrorDelProveedor(f"Fallo la consulta a Ollama: {exc}") from exc

        if respuesta.status_code == 404:
            raise ProveedorNoConfigurado(
                f"Ollama no tiene el modelo '{self._modelo}'. "
                f"Descarguelo con 'ollama pull {self._modelo}'."
            )
        if respuesta.status_code >= 400:
            raise ErrorDelProveedor(
                f"Ollama respondio {respuesta.status_code}: {respuesta.text[:200]}"
            )

        return self._traducir(respuesta.json())

    def _enviar(self, cuerpo: dict[str, Any]) -> httpx.Response:
        if self._cliente is not None:
            return self._cliente.post(self._url, json=cuerpo, timeout=self._espera)
        return httpx.post(self._url, json=cuerpo, timeout=self._espera)

    def _traducir(self, carga: dict[str, Any]) -> RespuestaDelModelo:
        mensaje = carga.get("message") or {}
        # Ollama informa tokens con estos dos nombres. Si el modelo no los
        # entrega, quedan en cero y la instrumentacion lo refleja como tal en vez
        # de estimarlos.
        entrada = int(carga.get("prompt_eval_count") or 0)
        salida = int(carga.get("eval_count") or 0)

        llamadas = mensaje.get("tool_calls") or []
        if llamadas:
            funcion = llamadas[0].get("function") or {}
            argumentos = funcion.get("arguments")
            # La API devuelve un objeto; algunas plantillas devuelven la cadena
            # JSON. Se aceptan ambos: rechazar la segunda seria descartar una
            # respuesta correcta por su envoltorio.
            if isinstance(argumentos, str):
                try:
                    argumentos = json.loads(argumentos)
                except json.JSONDecodeError:
                    argumentos = {}
            return RespuestaDelModelo(
                peticion=PeticionDeHerramienta(
                    nombre=str(funcion.get("name") or ""),
                    parametros=dict(argumentos or {}),
                ),
                tokens_entrada=entrada,
                tokens_salida=salida,
            )

        return RespuestaDelModelo(
            texto=str(mensaje.get("content") or ""),
            tokens_entrada=entrada,
            tokens_salida=salida,
        )

    def describir(self) -> dict[str, Any]:
        return {
            "proveedor": self.nombre,
            "modelo": self._modelo,
            "url": self._url,
            "ejecucion": "local: el dato del establecimiento no sale de la maquina",
            "precio_declarado": True,
            "usd_por_millon_entrada": self.usd_por_millon_entrada,
            "usd_por_millon_salida": self.usd_por_millon_salida,
        }
