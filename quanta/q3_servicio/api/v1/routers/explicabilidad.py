from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from q2_modelamiento import ArtefactoNoDisponible, VariableNoSimulable
from q3_servicio.api.v1.routers.prediccion import variables_o_error
from q3_servicio.core.seguridad import Usuario, exigir_jurisdiccion, usuario_actual
from q3_servicio.esquemas.predictivo import (
    RespuestaExplicacion,
    RespuestaSimulacion,
    SolicitudSimulacion,
)
from q3_servicio.servicios.motor import ServicioDePrediccion, servicio_de_prediccion

router = APIRouter(prefix="/xai", tags=["explicabilidad"])


@router.get("/{rbd}/shapley", response_model=RespuestaExplicacion)
def shapley(
    rbd: str,
    factor: str = "EFECTIVR",
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> RespuestaExplicacion:
    """Atribucion local: por que este establecimiento obtuvo este resultado."""
    exigir_jurisdiccion(rbd, usuario)
    variables = variables_o_error(servicio, rbd, periodo)
    try:
        return servicio.explicar(rbd, variables, factor)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except ArtefactoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, str(exc)) from exc


@router.post("/simular", response_model=RespuestaSimulacion)
def simular(
    solicitud: SolicitudSimulacion,
    usuario: Usuario = Depends(usuario_actual),
    servicio: ServicioDePrediccion = Depends(servicio_de_prediccion),
) -> RespuestaSimulacion:
    """Curva ICE: que ocurriria si el establecimiento modificara una variable."""
    exigir_jurisdiccion(solicitud.rbd, usuario)
    try:
        variables = variables_o_error(servicio, solicitud.rbd, None, solicitud.variables)
        return servicio.simular(
            solicitud.rbd, variables, solicitud.variable, solicitud.rango, solicitud.n_puntos
        )
    except (VariableNoSimulable, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except ArtefactoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
