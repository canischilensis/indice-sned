"""Rutas de establecimientos.

Capas cerradas (Richards y Ford, 2020, cap. 10, p. 135): la capa de rutas no
alcanza la persistencia. Toda lectura pasa por `ServicioDePrediccion`, que es la
fachada del cuanto 3. La clausura no es una convencion: es lo que permite que el
arnes de paridad reconstruya el servicio y con el se resuelva el adaptador activo
en un unico punto.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from q3_servicio.core.seguridad import Usuario, exigir_jurisdiccion, usuario_actual
from q3_servicio.esquemas.predictivo import RespuestaEstablecimientos, RespuestaRanking
from q3_servicio.repositorios import ConjuntoNoDisponible, EstablecimientoNoEncontrado
from q3_servicio.servicios.motor import ServicioDePrediccion, servicio_de_prediccion

router = APIRouter(prefix="/establecimientos", tags=["establecimientos"])


@router.get("", response_model=RespuestaEstablecimientos)
def mis_establecimientos(
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> dict:
    try:
        detalle = servicio.listar_establecimientos(usuario.rbds)
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return {
        "rol": usuario.rol.value,
        "rbds": usuario.rbds,
        "origen": servicio.origen_de_datos,
        "detalle": detalle,
    }


@router.get("/{rbd}")
def detalle(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> dict:
    exigir_jurisdiccion(rbd, usuario)
    try:
        return servicio.variables_de(rbd, periodo)
    except EstablecimientoNoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/{rbd}/ranking", response_model=RespuestaRanking)
def ranking(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> dict:
    """Posicion dentro del grupo homogeneo: la mecanica real de la seleccion."""
    exigir_jurisdiccion(rbd, usuario)
    try:
        return servicio.ranking_de(rbd, periodo)
    except EstablecimientoNoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
