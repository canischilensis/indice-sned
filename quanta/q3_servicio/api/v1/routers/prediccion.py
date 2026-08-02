from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from q2_modelamiento import ArtefactoNoDisponible
from q3_servicio.core.seguridad import Usuario, exigir_jurisdiccion, usuario_actual
from q3_servicio.esquemas.predictivo import RespuestaAlertas, RespuestaPrediccion
from q3_servicio.repositorios import ConjuntoNoDisponible, EstablecimientoNoEncontrado
from q3_servicio.servicios.motor import ServicioDePrediccion, servicio_de_prediccion

router = APIRouter(prefix="/prediccion", tags=["prediccion"])


def variables_o_error(servicio: ServicioDePrediccion, rbd: str, periodo: str | None, extra: dict | None = None) -> dict:
    """Traduce los errores del dominio a codigos HTTP. Unico lugar donde ocurre."""
    try:
        return servicio.variables_de(rbd, periodo, extra)
    except EstablecimientoNoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/{rbd}", response_model=RespuestaPrediccion)
def predecir(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> RespuestaPrediccion:
    exigir_jurisdiccion(rbd, usuario)
    variables = variables_o_error(servicio, rbd, periodo)
    try:
        return servicio.predecir(rbd, variables)
    except ArtefactoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/{rbd}/alertas", response_model=RespuestaAlertas)
def alertas(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> RespuestaAlertas:
    exigir_jurisdiccion(rbd, usuario)
    variables = variables_o_error(servicio, rbd, periodo)
    try:
        prediccion = servicio.predecir(rbd, variables)
    except ArtefactoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return RespuestaAlertas(rbd=rbd, alertas=servicio.evaluar_alertas(prediccion, variables))
