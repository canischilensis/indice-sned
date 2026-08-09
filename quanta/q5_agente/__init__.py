"""Cuanto 5 · Agente asesor de gestion.

Quinto cuanto logico del ecosistema. Se enchufa por el puerto AsesorDeGestion y
consulta las rutas publicadas del servicio como lo haria cualquier usuario: no
importa q2_modelamiento ni q3_servicio, y por lo tanto queda sometido a CTRL-04.

Si este cuanto se retira, el sistema sigue operando sin modificacion.
"""

from q5_agente.contrato import (
    AsesorDeGestion,
    Consulta,
    LlamadaHerramienta,
    RespuestaAsesor,
    Uso,
)
from q5_agente.errores import (
    CircuitoAbierto,
    ErrorDelAgente,
    ErrorDelProveedor,
    ErrorDelServicio,
    EstablecimientoNoEncontrado,
    FueraDeJurisdiccion,
    ParametroInvalido,
    RespuestaRechazada,
    ServicioNoDisponible,
    SesionExpirada,
)

__all__ = [
    "AsesorDeGestion",
    "CircuitoAbierto",
    "Consulta",
    "ErrorDelAgente",
    "ErrorDelProveedor",
    "ErrorDelServicio",
    "EstablecimientoNoEncontrado",
    "FueraDeJurisdiccion",
    "LlamadaHerramienta",
    "ParametroInvalido",
    "RespuestaAsesor",
    "RespuestaRechazada",
    "ServicioNoDisponible",
    "SesionExpirada",
    "Uso",
]
