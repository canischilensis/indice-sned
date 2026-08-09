"""Decoradores del proveedor: instrumentacion y cortacircuitos.

Ambos implementan el mismo puerto que envuelven, de modo que el bucle no sabe
cuantas capas hay debajo. Es el mismo mecanismo que el cuanto 2 usa para
auditar y memorizar inferencias.

Sobre el cortacircuitos: el repositorio lo habia descartado con un argumento
explicito —"no hay llamadas a servicios externos en tiempo de ejecucion"—. Con
el agente ese argumento deja de ser cierto, y por eso se implementa aqui. La
decision queda registrada en ADR-006.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from q5_agente.errores import CircuitoAbierto, ErrorDelProveedor
from q5_agente.proveedores.contrato import Mensaje, ProveedorDeModelo, RespuestaDelModelo


@dataclass
class Consumo:
    """Acumulador de la instrumentacion. Se lee al cierre de cada consulta."""

    tokens_entrada: int = 0
    tokens_salida: int = 0
    costo_usd: float = 0.0
    llamadas: int = 0
    milisegundos: int = 0
    por_llamada: list[dict[str, Any]] = field(default_factory=list)


class ProveedorInstrumentado(ProveedorDeModelo):
    """Decorator: mide tokens, costo y latencia desde el primer dia."""

    def __init__(
        self, envuelto: ProveedorDeModelo, reloj: Callable[[], float] | None = None
    ) -> None:
        self._envuelto = envuelto
        self._reloj = reloj or time.monotonic
        self.consumo = Consumo()
        self.nombre = f"instrumentado({envuelto.nombre})"
        self.usd_por_millon_entrada = envuelto.usd_por_millon_entrada
        self.usd_por_millon_salida = envuelto.usd_por_millon_salida

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        inicio = self._reloj()
        respuesta = self._envuelto.completar(mensajes, herramientas)
        transcurrido = int((self._reloj() - inicio) * 1000)

        costo = self._envuelto.costo(respuesta.tokens_entrada, respuesta.tokens_salida)
        self.consumo.tokens_entrada += respuesta.tokens_entrada
        self.consumo.tokens_salida += respuesta.tokens_salida
        self.consumo.costo_usd = round(self.consumo.costo_usd + costo, 8)
        self.consumo.llamadas += 1
        self.consumo.milisegundos += transcurrido
        self.consumo.por_llamada.append(
            {
                "tokens_entrada": respuesta.tokens_entrada,
                "tokens_salida": respuesta.tokens_salida,
                "costo_usd": costo,
                "milisegundos": transcurrido,
                "pidio_herramienta": respuesta.quiere_herramienta,
            }
        )
        return respuesta

    def reiniciar(self) -> None:
        self.consumo = Consumo()

    def describir(self) -> dict[str, Any]:
        return {"proveedor": self.nombre, "llamadas": self.consumo.llamadas}


class ProveedorConCortacircuitos(ProveedorDeModelo):
    """Circuit Breaker sobre la dependencia externa.

    Tres estados. Cerrado: pasa. Abierto: corta sin intentar, durante la ventana
    de reposo. Semiabierto: deja pasar una sola llamada de sondeo; si tiene
    exito cierra, si falla vuelve a abrir.
    """

    CERRADO, ABIERTO, SEMIABIERTO = "cerrado", "abierto", "semiabierto"

    def __init__(
        self,
        envuelto: ProveedorDeModelo,
        umbral_fallos: int = 3,
        segundos_reposo: float = 30.0,
        reloj: Callable[[], float] | None = None,
    ) -> None:
        self._envuelto = envuelto
        self._umbral = umbral_fallos
        self._reposo = segundos_reposo
        self._reloj = reloj or time.monotonic
        self._fallos = 0
        self._abierto_desde: float | None = None
        self.nombre = f"cortacircuitos({envuelto.nombre})"
        self.usd_por_millon_entrada = envuelto.usd_por_millon_entrada
        self.usd_por_millon_salida = envuelto.usd_por_millon_salida

    @property
    def estado(self) -> str:
        if self._abierto_desde is None:
            return self.CERRADO
        if self._reloj() - self._abierto_desde >= self._reposo:
            return self.SEMIABIERTO
        return self.ABIERTO

    def completar(
        self, mensajes: list[Mensaje], herramientas: list[dict[str, Any]]
    ) -> RespuestaDelModelo:
        estado = self.estado
        if estado == self.ABIERTO:
            restante = self._reposo - (self._reloj() - (self._abierto_desde or 0))
            raise CircuitoAbierto(
                f"El proveedor esta marcado como caido; reintente en {max(0, restante):.0f} s."
            )
        try:
            respuesta = self._envuelto.completar(mensajes, herramientas)
        except ErrorDelProveedor:
            self._registrar_fallo()
            raise
        self._registrar_exito()
        return respuesta

    def _registrar_fallo(self) -> None:
        self._fallos += 1
        if self._fallos >= self._umbral:
            self._abierto_desde = self._reloj()

    def _registrar_exito(self) -> None:
        self._fallos = 0
        self._abierto_desde = None

    def describir(self) -> dict[str, Any]:
        return {"proveedor": self.nombre, "estado": self.estado, "fallos": self._fallos}
