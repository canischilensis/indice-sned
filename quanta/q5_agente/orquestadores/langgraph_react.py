"""Segundo adaptador del puerto `AsesorDeGestion`, construido sobre LangGraph.

Existe para responder una pregunta con numeros: **que aporta un framework de
orquestacion sobre un bucle de sesenta lineas escrito a mano, y que cuesta**. Los
veinte casos criticos evalúan a los dos sin modificarse, porque estan escritos
contra el puerto y no contra su implementacion. Esa es la deuda que un puerto con
un solo adaptador tiene pendiente, y aqui se cobra.

Se usa `create_react_agent`, el grafo que LangGraph trae de fabrica, y no uno
construido a mano. Es lo que corresponde comparar: la pregunta no es si se puede
reproducir el bucle con la libreria —se puede—, sino que entrega la libreria
cuando se la usa como la usaria cualquiera.

## La condicion que hace valida la comparacion

**Solo se mueve una variable.** Este adaptador reutiliza, sin reimplementar
ninguna:

- el catalogo de herramientas y la puerta HTTP del cuanto 5,
- `PoliticaDeSalida` con G-01, G-02 y G-03,
- la normalizacion a prosa plana,
- `cifras_del_contexto`, la regla que admite las cifras del propio pedido.

Si reescribiera cualquiera de esas, la medicion dejaria de comparar orquestacion
y pasaria a comparar dos sistemas distintos.

## Por que hay un envoltorio de modelo y no se usa el cliente de LangChain

`create_react_agent` espera un `BaseChatModel`. Lo directo seria pasarle
`ChatGoogleGenerativeAI`, y entonces se moverian **dos** variables a la vez:
orquestador y cliente del proveedor. La comparacion mediria una mezcla.

`_ModeloDesdeProveedor` presenta el puerto `ProveedorDeModelo` —el mismo que usa
el bucle propio— con la interfaz que LangGraph espera. Cuesta unas cien lineas y
compra dos cosas: la comparacion aisla la orquestacion, y el adaptador
determinista tambien corre bajo LangGraph, de modo que los veinte casos se
ejecutan sin red, sin clave y sin costo.

Es la tercera vez en el proyecto que un puerto se paga solo.

## Dependencias

`langgraph` y `langchain-core` son pesadas y **opcionales**. Este modulo se
importa de forma perezosa desde la fabrica, igual que los SDK de Anthropic,
OpenAI y Gemini. La consola sigue arrancando con `httpx` como unica dependencia
mientras el orquestador configurado sea el bucle propio.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.prebuilt import create_react_agent

from q5_agente.contrato import (
    AsesorDeGestion,
    Consulta,
    LlamadaHerramienta,
    RespuestaAsesor,
    Uso,
    cifras_del_contexto,
)
from q5_agente.errores import CircuitoAbierto, ErrorDelProveedor, ParametroInvalido
from q5_agente.guardarrailes import PoliticaDeSalida
from q5_agente.herramientas.contrato import Herramienta, ResultadoHerramienta
from q5_agente.prompts import SISTEMA, formatear_consulta
from q5_agente.proveedores.contrato import Mensaje, ProveedorDeModelo
from q5_agente.redaccion import a_prosa_plana

_DISCULPA_PROVEEDOR = (
    "No pude consultar al proveedor de lenguaje y por lo tanto no puedo responder. "
    "Las cifras del establecimiento siguen disponibles en el tablero."
)


def _a_mensajes(mensajes: Sequence[BaseMessage]) -> list[Mensaje]:
    """Traduce la conversacion de LangChain al vocabulario del puerto.

    El adaptador determinista busca el ultimo mensaje de usuario y el ultimo de
    herramienta; los demas roles viajan para que un proveedor externo tenga la
    conversacion completa.
    """
    traducidos: list[Mensaje] = []
    for mensaje in mensajes:
        contenido = mensaje.content if isinstance(mensaje.content, str) else str(mensaje.content)
        if isinstance(mensaje, SystemMessage):
            traducidos.append(Mensaje("sistema", contenido))
        elif isinstance(mensaje, HumanMessage):
            traducidos.append(Mensaje("usuario", contenido))
        elif isinstance(mensaje, ToolMessage):
            traducidos.append(Mensaje("herramienta", contenido))
        elif isinstance(mensaje, AIMessage) and contenido:
            traducidos.append(Mensaje("asistente", contenido))
    return traducidos


class _ModeloDesdeProveedor(BaseChatModel):
    """Presenta un `ProveedorDeModelo` con la interfaz que LangGraph espera.

    Adapter en el sentido estricto: no agrega comportamiento, traduce dos
    vocabularios. La decision de que herramienta llamar la sigue tomando el mismo
    proveedor que usa el bucle propio.
    """

    model_config = {"arbitrary_types_allowed": True}

    proveedor: Any
    catalogo: list[dict[str, Any]] = []

    @property
    def _llm_type(self) -> str:
        return f"puerto-proveedor-{getattr(self.proveedor, 'nombre', 'desconocido')}"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> _ModeloDesdeProveedor:
        """Traduce las herramientas de LangChain al catalogo que el puerto entiende.

        LangGraph declara las herramientas en su formato; el puerto las espera
        como nombre, descripcion y esquema. La traduccion ocurre una vez, aqui, y
        el proveedor recibe exactamente el mismo catalogo que recibiria del bucle
        propio: es lo que hace comparables las dos ejecuciones.
        """
        catalogo: list[dict[str, Any]] = []
        for herramienta in tools:
            declarada = convert_to_openai_tool(herramienta)["function"]
            catalogo.append(
                {
                    "nombre": declarada["name"],
                    "descripcion": declarada.get("description", ""),
                    "esquema": declarada.get("parameters", {}),
                }
            )
        return self.model_copy(update={"catalogo": catalogo})

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        respuesta = self.proveedor.completar(_a_mensajes(messages), self.catalogo)

        if respuesta.quiere_herramienta:
            peticion = respuesta.peticion
            mensaje = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": peticion.nombre,
                        "args": dict(peticion.parametros),
                        # Identificador estable y no aleatorio: dos ejecuciones
                        # del mismo caso deben producir la misma traza.
                        "id": f"{peticion.nombre}-{len(messages)}",
                        "type": "tool_call",
                    }
                ],
            )
        else:
            mensaje = AIMessage(content=respuesta.texto or "")

        mensaje.usage_metadata = {
            "input_tokens": respuesta.tokens_entrada,
            "output_tokens": respuesta.tokens_salida,
            "total_tokens": respuesta.tokens_entrada + respuesta.tokens_salida,
        }
        return ChatResult(generations=[ChatGeneration(message=mensaje)])


class AgenteLangGraph(AsesorDeGestion):
    """Adaptador del puerto sobre el agente ReAct que LangGraph trae de fabrica."""

    nombre = "langgraph_react"

    def __init__(
        self,
        proveedor: ProveedorDeModelo,
        herramientas: dict[str, Herramienta],
        politica: PoliticaDeSalida | None = None,
        max_pasos: int = 3,
        reloj: Callable[[], float] | None = None,
    ) -> None:
        self._proveedor = proveedor
        self._herramientas = herramientas
        self._politica = politica or PoliticaDeSalida()
        self._max_pasos = max_pasos
        self._reloj = reloj or time.monotonic

    # --- puerto -----------------------------------------------------------

    def asesorar(self, consulta: Consulta) -> RespuestaAsesor:
        llamadas: list[LlamadaHerramienta] = []
        cifras: set[float] = cifras_del_contexto(consulta)
        diagnostico: set[float] = set()

        herramientas = [
            self._como_herramienta_de_langchain(h, consulta, llamadas, cifras, diagnostico)
            for h in self._herramientas.values()
        ]
        modelo = _ModeloDesdeProveedor(proveedor=self._proveedor)
        grafo = create_react_agent(modelo, herramientas, prompt=SISTEMA)

        try:
            estado = grafo.invoke(
                {"messages": [HumanMessage(content=formatear_consulta(consulta))]},
                # ReAct recorre dos nodos por paso —modelo y herramientas— mas el
                # turno final de redaccion. El presupuesto del puerto se expresa
                # en pasos, no en nodos, y aqui se traduce.
                {"recursion_limit": 2 * self._max_pasos + 1},
            )
        except (CircuitoAbierto, ErrorDelProveedor) as exc:
            return RespuestaAsesor(
                texto=f"{_DISCULPA_PROVEEDOR} Motivo tecnico: {exc}",
                llamadas=llamadas,
                uso=self._uso([]),
                guardarrailes_aplicados=["G-04"],
                rechazada=True,
                motivo_rechazo=str(exc),
            )

        mensajes = estado.get("messages", [])
        texto = ""
        for mensaje in reversed(mensajes):
            if isinstance(mensaje, AIMessage) and isinstance(mensaje.content, str):
                if mensaje.content.strip():
                    texto = mensaje.content
                    break

        return self._cerrar(texto, llamadas, cifras, diagnostico, self._uso(mensajes))

    def describir(self) -> dict[str, Any]:
        return {
            "asesor": self.nombre,
            "orquestador": "langgraph.prebuilt.create_react_agent",
            "proveedor": getattr(self._proveedor, "nombre", "desconocido"),
            "max_pasos": self._max_pasos,
        }

    # --- herramientas -----------------------------------------------------

    def _como_herramienta_de_langchain(
        self,
        herramienta: Herramienta,
        consulta: Consulta,
        llamadas: list[LlamadaHerramienta],
        cifras: set[float],
        diagnostico: set[float],
    ) -> StructuredTool:
        """Envuelve una herramienta del catalogo sin duplicar su logica.

        La ejecucion real sigue siendo la del cuanto 5. Lo que se agrega aqui es
        el registro de la traza y la acumulacion de cifras, que es lo que despues
        alimenta a G-02.
        """

        def ejecutar(**parametros: Any) -> str:
            inicio = self._reloj()

            # El RBD de la sesion manda sobre el que el modelo haya podido
            # inferir. Misma regla que el bucle propio, y no es cosmetica: es lo
            # que impide que una consulta alcance un establecimiento ajeno
            # porque el modelo leyo un numero en el texto.
            efectivos = dict(parametros)
            efectivos["rbd"] = consulta.rbd
            if consulta.periodo and not efectivos.get("periodo"):
                efectivos["periodo"] = consulta.periodo

            try:
                resultado = herramienta.ejecutar(**efectivos)
            except ParametroInvalido as exc:
                resultado = ResultadoHerramienta.fallida(herramienta.nombre, str(exc))

            cifras.update(resultado.cifras)
            diagnostico.update(resultado.cifras_diagnostico)
            llamadas.append(
                LlamadaHerramienta(
                    herramienta=herramienta.nombre,
                    parametros=efectivos,
                    exito=resultado.exito,
                    resumen=resultado.error or f"{len(resultado.cifras)} cifras recibidas",
                    milisegundos=int((self._reloj() - inicio) * 1000),
                )
            )
            return json.dumps(
                {
                    "herramienta": resultado.herramienta,
                    "exito": resultado.exito,
                    "error": resultado.error,
                    "origen": resultado.origen,
                    "datos": resultado.datos,
                },
                ensure_ascii=False,
            )

        return StructuredTool(
            name=herramienta.nombre,
            description=herramienta.descripcion,
            args_schema=herramienta.esquema(),
            func=ejecutar,
        )

    # --- cierre -----------------------------------------------------------

    def _uso(self, mensajes: Sequence[BaseMessage]) -> Uso:
        entrada = salida = llamadas = 0
        for mensaje in mensajes:
            uso = getattr(mensaje, "usage_metadata", None)
            if not uso:
                continue
            entrada += uso.get("input_tokens", 0)
            salida += uso.get("output_tokens", 0)
            llamadas += 1
        return Uso(
            tokens_entrada=entrada,
            tokens_salida=salida,
            costo_usd=self._proveedor.costo(entrada, salida),
            llamadas_al_modelo=llamadas,
        )

    def _cerrar(
        self,
        texto: str,
        llamadas: list[LlamadaHerramienta],
        cifras: set[float],
        diagnostico: set[float],
        uso: Uso,
    ) -> RespuestaAsesor:
        """Identico al cierre del bucle propio, y esa identidad es deliberada.

        Normalizar antes de evaluar, evaluar sobre el conjunto de cifras de dato
        mas las de mensajes del sistema, y retirar la respuesta entera si no
        pasa. Si este adaptador cerrara con otro criterio, la comparacion mediria
        dos politicas de salida en vez de dos orquestadores.
        """
        if not texto.strip():
            texto = "No consegui cerrar la consulta dentro del limite de pasos previsto."

        texto = a_prosa_plana(texto)
        aceptado, codigo, motivo = self._politica.evaluar(texto, cifras | diagnostico)
        if not aceptado:
            return RespuestaAsesor(
                texto=(
                    "Retire la respuesta antes de entregarla porque no cumplia la politica de "
                    "salida del sistema. Puede consultar las cifras directamente en el tablero."
                ),
                llamadas=llamadas,
                uso=uso,
                guardarrailes_aplicados=[codigo or "G-00"],
                rechazada=True,
                motivo_rechazo=motivo,
            )
        return RespuestaAsesor(
            texto=texto,
            llamadas=llamadas,
            uso=uso,
            cifras_citadas=sorted(cifras),
            cifras_de_diagnostico=sorted(diagnostico),
            guardarrailes_aplicados=["G-01", "G-02", "G-03"],
        )
