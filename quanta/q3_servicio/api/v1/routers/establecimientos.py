from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from q3_servicio.core.seguridad import Usuario, exigir_jurisdiccion, usuario_actual
from q3_servicio.repositorios import (
    ConjuntoNoDisponible,
    EstablecimientoNoEncontrado,
    RepositorioEstablecimientos,
    obtener_repositorio,
)

router = APIRouter(prefix="/establecimientos", tags=["establecimientos"])


def repositorio() -> RepositorioEstablecimientos:
    """Adaptador activo, resuelto por REPOSITORIO_DATOS."""
    return obtener_repositorio()


@router.get("")
def mis_establecimientos(
    usuario: Usuario = Depends(usuario_actual),
    repo: RepositorioEstablecimientos = Depends(repositorio),
) -> dict:
    try:
        detalle = repo.listar(usuario.rbds)
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return {"rol": usuario.rol.value, "rbds": usuario.rbds, "origen": repo.origen, "detalle": detalle}


@router.get("/{rbd}")
def detalle(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    repo: RepositorioEstablecimientos = Depends(repositorio),
) -> dict:
    exigir_jurisdiccion(rbd, usuario)
    try:
        return repo.obtener(rbd, periodo)
    except EstablecimientoNoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/{rbd}/ranking")
def ranking(
    rbd: str,
    periodo: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    repo: RepositorioEstablecimientos = Depends(repositorio),
) -> dict:
    """Posicion dentro del grupo homogeneo: la mecanica real de la seleccion."""
    exigir_jurisdiccion(rbd, usuario)
    try:
        return repo.ranking(rbd, periodo)
    except EstablecimientoNoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ConjuntoNoDisponible as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
