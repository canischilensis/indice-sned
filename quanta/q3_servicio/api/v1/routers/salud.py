from __future__ import annotations

from fastapi import APIRouter, Depends

from q2_modelamiento import estrategias_disponibles, registro
from q2_modelamiento.catalogo import cargar_catalogo
from q3_servicio import __version__
from q3_servicio.servicios.motor import ServicioDePrediccion, servicio_de_prediccion

router = APIRouter(tags=["salud"])


@router.get("/salud")
def salud() -> dict:
    return {"estado": "operativo", "version": __version__}


@router.get("/salud/registro")
def registro_modelos() -> dict:
    """Inventario del registro de artefactos — evidencia de CTRL-05.

    `materializado` revela cuales han sido deserializados: con el proxy virtual,
    el arranque no carga ninguno.
    """
    artefactos = registro().inventario()
    return {
        "estrategias": estrategias_disponibles(),
        "n_artefactos": len(artefactos),
        "n_materializados": sum(1 for a in artefactos if a["materializado"]),
        "artefactos": artefactos,
        "nota": "Los artefactos no se versionan en git; sus metadatos si.",
    }


@router.get("/salud/composicion")
def composicion(servicio: ServicioDePrediccion = Depends(servicio_de_prediccion)) -> dict:
    """Cadena de decoradores y adaptadores activos. Hace visible la composicion."""
    return servicio.describir()


@router.get("/catalogo/factores")
def catalogo() -> dict:
    """Ponderaciones oficiales como DATO. Decision de normalizacion 3."""
    return cargar_catalogo()
