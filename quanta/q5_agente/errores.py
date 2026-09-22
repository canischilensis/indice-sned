"""Errores del cuanto 5.

Traducen las condiciones del servicio y del proveedor externo a excepciones del
dominio del agente, para que el bucle no razone sobre codigos HTTP ni sobre
detalles del SDK de ningun proveedor.
"""

from __future__ import annotations


class ErrorDelAgente(Exception):
    """Raiz de la jerarquia. Permite capturar todo el cuanto de una vez."""


# --- fallos que provienen del servicio (Q3) ---------------------------------


class ErrorDelServicio(ErrorDelAgente):
    """El servicio respondio, pero con una condicion que el agente debe acatar."""


class SesionExpirada(ErrorDelServicio):
    """401. El token vencio o no se emitio."""


class FueraDeJurisdiccion(ErrorDelServicio):
    """403. CTRL-04: el RBD no pertenece al usuario. Nunca se convierte en 404."""


class EstablecimientoNoEncontrado(ErrorDelServicio):
    """404. El RBD esta en la jurisdiccion pero no en el conjunto depurado."""


class ParametroInvalido(ErrorDelServicio):
    """422. Variable no simulable o valor fuera del dominio admisible."""


class ServicioNoDisponible(ErrorDelServicio):
    """503. Artefacto o conjunto de datos no disponible."""


# --- fallos que provienen del proveedor de modelo ---------------------------


class ErrorDelProveedor(ErrorDelAgente):
    """El proveedor externo fallo. Es la dependencia que el sistema no tenia."""


class ProveedorNoConfigurado(ErrorDelProveedor):
    """Falta la credencial o el paquete del proveedor solicitado."""


class CircuitoAbierto(ErrorDelProveedor):
    """El cortacircuitos corto la llamada sin intentarla."""


# --- fallos de politica -----------------------------------------------------


class RespuestaRechazada(ErrorDelAgente):
    """Un guardarrail rechazo la salida generada. Contiene el motivo."""

    def __init__(self, motivo: str, codigo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.codigo = codigo
