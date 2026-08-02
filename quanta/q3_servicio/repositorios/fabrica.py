"""Factoria de adaptadores del puerto RepositorioEstablecimientos.

Este modulo es el UNICO interruptor entre almacenamientos. Vive en la capa de
infraestructura: ni el dominio (cuanto 2) ni los casos de uso (ServicioDePrediccion)
conocen su existencia ni el nombre de la variable de entorno.

    REPOSITORIO_DATOS=postgres   (predeterminado)
    REPOSITORIO_DATOS=parquet    (desarrollo, notebooks, demostracion sin base)

Ambos adaptadores quedan operativos y conmutables. Que el sistema funcione
identico con los dos es la verificacion empirica del patron Repository
(Fowler, 2002): la capa de servicio no sabe de donde viene el dato.
"""

from __future__ import annotations

import os

from q3_servicio.repositorios.contrato import RepositorioEstablecimientos
from q3_servicio.repositorios.parquet import RepositorioParquet
from q3_servicio.repositorios.postgres import RepositorioPostgres

ADAPTADORES: dict[str, type[RepositorioEstablecimientos]] = {
    "parquet": RepositorioParquet,
    "postgres": RepositorioPostgres,
}

PREDETERMINADO = "postgres"


class AdaptadorNoRegistrado(ValueError):
    pass


def nombre_adaptador_activo() -> str:
    return os.getenv("REPOSITORIO_DATOS", PREDETERMINADO).strip().lower()


def obtener_repositorio(nombre: str | None = None) -> RepositorioEstablecimientos:
    """Construye el adaptador indicado por configuracion.

    Sin cache deliberadamente: las pruebas de paridad conmutan el interruptor
    dentro del mismo proceso y necesitan que el cambio surta efecto.
    """
    clave = (nombre or nombre_adaptador_activo())
    if clave not in ADAPTADORES:
        raise AdaptadorNoRegistrado(
            f"REPOSITORIO_DATOS='{clave}' no existe. Disponibles: {sorted(ADAPTADORES)}"
        )
    return ADAPTADORES[clave]()
