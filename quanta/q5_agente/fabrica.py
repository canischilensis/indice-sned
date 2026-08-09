"""Fabrica del cuanto 5: arma el agente completo desde la configuracion.

Registro explicito de proveedores, del mismo modo que el cuanto 3 resuelve su
repositorio por clave. Añadir un proveedor es agregar una entrada, no tocar el
bucle.
"""

from __future__ import annotations

from collections.abc import Callable

from q5_agente.bucle import AgenteDeBucleSimple
from q5_agente.config import ConfiguracionDelAgente, config_agente
from q5_agente.contrato import AsesorDeGestion
from q5_agente.decoradores import ProveedorConCortacircuitos, ProveedorInstrumentado
from q5_agente.errores import ProveedorNoConfigurado
from q5_agente.gateway import PuertaDeServicio, ServicioSnedGateway
from q5_agente.guardarrailes import PoliticaDeSalida, SanitizadorDeParametros
from q5_agente.herramientas.catalogo import construir_catalogo
from q5_agente.proveedores.contrato import ProveedorDeModelo
from q5_agente.proveedores.determinista import AdaptadorDeterminista

PREDETERMINADO = "determinista"


def _determinista(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    return AdaptadorDeterminista()


def _anthropic(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    from q5_agente.proveedores.externos import AdaptadorAnthropic

    return AdaptadorAnthropic(modelo=cfg.agente_modelo or "claude-sonnet-4-5")


def _openai(cfg: ConfiguracionDelAgente) -> ProveedorDeModelo:
    from q5_agente.proveedores.externos import AdaptadorOpenAI

    return AdaptadorOpenAI(modelo=cfg.agente_modelo or "gpt-4.1")


PROVEEDORES: dict[str, Callable[[ConfiguracionDelAgente], ProveedorDeModelo]] = {
    "determinista": _determinista,
    "anthropic": _anthropic,
    "openai": _openai,
}


def crear_proveedor(cfg: ConfiguracionDelAgente | None = None) -> ProveedorDeModelo:
    cfg = cfg or config_agente()
    constructor = PROVEEDORES.get(cfg.agente_proveedor)
    if constructor is None:
        raise ProveedorNoConfigurado(
            f"Proveedor '{cfg.agente_proveedor}' desconocido. "
            f"Disponibles: {', '.join(sorted(PROVEEDORES))}."
        )
    return constructor(cfg)


def crear_puerta(cfg: ConfiguracionDelAgente | None = None) -> PuertaDeServicio:
    cfg = cfg or config_agente()
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
) -> AsesorDeGestion:
    """Arma la cadena completa: cortacircuitos -> instrumentacion -> proveedor."""
    cfg = cfg or config_agente()
    herramientas = construir_catalogo(puerta or crear_puerta(cfg), SanitizadorDeParametros())
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
    return AgenteDeBucleSimple(protegido, herramientas, politica, max_pasos=cfg.agente_max_pasos)
