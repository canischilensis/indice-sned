"""Fabrica del cuanto 5: arma el agente completo desde la configuracion.

Registro explicito de proveedores, del mismo modo que el cuanto 3 resuelve su
repositorio por clave. Añadir un proveedor es agregar una entrada, no tocar el
bucle.
"""

from __future__ import annotations

from collections.abc import Callable

from q5_agente.bucle import AgenteDeBucleSimple
from q5_agente.config import ConfiguracionDelAgente, config_agente, secreto
from q5_agente.contrato import AsesorDeGestion
from q5_agente.decoradores import ProveedorConCortacircuitos, ProveedorInstrumentado
from q5_agente.errores import ErrorDelAgente, ProveedorNoConfigurado
from q5_agente.gateway import PuertaDeServicio, ServicioSnedGateway
from q5_agente.guardarrailes import PoliticaDeSalida, SanitizadorDeParametros
from q5_agente.herramientas.catalogo import construir_catalogo
from q5_agente.herramientas.contrato import Herramienta
from q5_agente.proveedores.contrato import ProveedorDeModelo
from q5_agente.proveedores.determinista import AdaptadorDeterminista

PREDETERMINADO = "determinista"


class OrquestadorDesconocido(ErrorDelAgente):
    """El orquestador pedido no esta en el registro.

    Falla al construir y no a media consulta, con la lista de los disponibles:
    un nombre mal escrito en el entorno debe decir que escribir, no dejar al
    usuario adivinando por que el agente no responde.
    """


def _determinista(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    return AdaptadorDeterminista()


def _anthropic(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    from q5_agente.proveedores.externos import AdaptadorAnthropic

    return AdaptadorAnthropic(
        modelo=cfg.agente_modelo or "claude-sonnet-4-5",
        clave=secreto("ANTHROPIC_API_KEY"),
    )


def _openai(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    from q5_agente.proveedores.externos import AdaptadorOpenAI

    return AdaptadorOpenAI(
        modelo=cfg.agente_modelo or "gpt-4.1",
        clave=secreto("OPENAI_API_KEY"),
    )


def _gemini(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    from q5_agente.proveedores.externos import AdaptadorGemini

    return AdaptadorGemini(
        modelo=cfg.agente_modelo or AdaptadorGemini.MODELO_PREDETERMINADO,
        clave=secreto("GEMINI_API_KEY") or secreto("GOOGLE_API_KEY"),
    )


PROVEEDORES: dict[str, Callable[[ConfiguracionDelAgente], ProveedorDeModelo]] = {
    "determinista": _determinista,
    "anthropic": _anthropic,
    "openai": _openai,
    "gemini": _gemini,
}


#: Prefijos de nombre de modelo, por proveedor. Solo sirven para reconocer una
#: confusion frecuente y decirlo: 'gemini-3.6-flash' es un modelo, no un
#: proveedor. No se usan para adivinar ni para corregir nada por cuenta propia.
_PREFIJOS_DE_MODELO = {
    "gemini": ("gemini-", "gemma-"),
    "anthropic": ("claude-",),
    "openai": ("gpt-", "o1-", "o3-", "o4-"),
}


def _proveedor_de(nombre_de_modelo: str) -> str | None:
    for proveedor, prefijos in _PREFIJOS_DE_MODELO.items():
        if nombre_de_modelo.startswith(prefijos):
            return proveedor
    return None


def crear_proveedor(cfg: ConfiguracionDelAgente | None = None) -> ProveedorDeModelo:
    cfg = cfg or config_agente()
    constructor = PROVEEDORES.get(cfg.agente_proveedor)
    if constructor is not None:
        return constructor(cfg)

    disponibles = ", ".join(sorted(PROVEEDORES))
    # Confundir las dos variables cuesta caro: el mensaje "proveedor
    # desconocido" es cierto pero inutil cuando lo que hay escrito es,
    # claramente, el nombre de un modelo.
    probable = _proveedor_de(cfg.agente_proveedor)
    if probable:
        raise ProveedorNoConfigurado(
            f"'{cfg.agente_proveedor}' es un MODELO, no un proveedor. Son dos "
            f"variables distintas:\n"
            f"    AGENTE_PROVEEDOR={probable}\n"
            f"    AGENTE_MODELO={cfg.agente_proveedor}\n"
            f"Proveedores disponibles: {disponibles}."
        )
    raise ProveedorNoConfigurado(
        f"Proveedor '{cfg.agente_proveedor}' desconocido. Disponibles: {disponibles}."
    )


def crear_puerta(
    cfg: ConfiguracionDelAgente | None = None, token: str | None = None
) -> PuertaDeServicio:
    """Gateway con identidad delegada si llega un token; propia si no llega.

    La interfaz debe pasar SIEMPRE el token del usuario. La consola no lo tiene
    y usa la cuenta de servicio, que es lo correcto porque ahi no hay un usuario
    a quien proteger.
    """
    cfg = cfg or config_agente()
    if token:
        return ServicioSnedGateway(
            base_url=cfg.agente_base_url,
            token=token,
            prefijo=cfg.agente_prefijo_api,
            segundos_espera=cfg.agente_segundos_espera,
        )
    return ServicioSnedGateway(
        base_url=cfg.agente_base_url,
        usuario=cfg.agente_usuario,
        clave=cfg.agente_clave,
        prefijo=cfg.agente_prefijo_api,
        segundos_espera=cfg.agente_segundos_espera,
    )


def crear_agente(
    cfg: ConfiguracionDelAgente | None = None,
    puerta: PuertaDeServicio | None = None,
    proveedor: ProveedorDeModelo | None = None,
    token: str | None = None,
) -> AsesorDeGestion:
    """Arma la cadena completa: cortacircuitos -> instrumentacion -> proveedor."""
    cfg = cfg or config_agente()
    herramientas = construir_catalogo(
        puerta or crear_puerta(cfg, token), SanitizadorDeParametros()
    )
    base = proveedor or crear_proveedor(cfg)
    if isinstance(base, AdaptadorDeterminista):
        # El proveedor determinista rutea con los disparadores del catalogo real,
        # de modo que agregar una herramienta no exige tocar el proveedor.
        base = AdaptadorDeterminista({h.nombre: h.disparadores for h in herramientas.values()})
    instrumentado = ProveedorInstrumentado(base)
    protegido = ProveedorConCortacircuitos(
        instrumentado,
        umbral_fallos=cfg.agente_umbral_fallos,
        segundos_reposo=cfg.agente_segundos_reposo,
    )
    politica = PoliticaDeSalida(
        fundamentacion=cfg.agente_guardarrail_cifras,
        promesas=cfg.agente_guardarrail_promesas,
    )

    constructor = ORQUESTADORES.get(cfg.agente_orquestador)
    if constructor is None:
        raise OrquestadorDesconocido(
            f"AGENTE_ORQUESTADOR='{cfg.agente_orquestador}' no existe. "
            f"Disponibles: {sorted(ORQUESTADORES)}"
        )
    return constructor(protegido, herramientas, politica, cfg.agente_max_pasos)


def _bucle_simple(
    proveedor: ProveedorDeModelo,
    herramientas: dict[str, Herramienta],
    politica: PoliticaDeSalida,
    max_pasos: int,
) -> AsesorDeGestion:
    return AgenteDeBucleSimple(proveedor, herramientas, politica, max_pasos=max_pasos)


def _langgraph_react(
    proveedor: ProveedorDeModelo,
    herramientas: dict[str, Herramienta],
    politica: PoliticaDeSalida,
    max_pasos: int,
) -> AsesorDeGestion:
    """Importacion perezosa, igual que la de los SDK de los proveedores.

    `langgraph` arrastra `pydantic` y la pila de `langchain`, que la compuerta
    prohibe en el cuanto 5. La prohibicion se respeta porque este modulo no se
    importa nunca salvo que la configuracion lo pida: la consola arranca con
    `httpx` como unica dependencia mientras el orquestador sea el bucle propio, y
    `tests/arquitectura/` lo verifica sin necesitar excepciones.
    """
    from q5_agente.orquestadores.langgraph_react import AgenteLangGraph  # noqa: PLC0415

    return AgenteLangGraph(proveedor, herramientas, politica, max_pasos=max_pasos)


#: Registro de orquestadores. Dos adaptadores del mismo puerto: el bucle escrito
#: a mano y el ReAct de LangGraph. Existe para medir la diferencia, no para
#: elegir un ganador de antemano.
ORQUESTADORES: dict[str, Callable[..., AsesorDeGestion]] = {
    "bucle_simple": _bucle_simple,
    "langgraph_react": _langgraph_react,
}
