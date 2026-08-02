"""Registro de modelos serializados — CTRL-05.

Patron Registry (Fowler, 2002): "un objeto bien conocido que otros objetos
pueden usar para encontrar objetos y servicios comunes". Sustituye
funcionalmente a una plataforma de Model Registry sin incorporar la carga
operativa de una infraestructura de orquestacion, que para un fenomeno de
calculo bianual seria por si misma una fuente de deuda tecnica (Huyen, 2022).

Los artefactos se entregan envueltos en un ArtefactoDiferido (Virtual Proxy),
de modo que el arranque del servicio no depende del tamano del registro.

Nota de diseno: Registry comparte los riesgos del Singleton. Se mitiga
permitiendo instanciarlo con rutas alternativas, para que las pruebas usen un
registro temporal en lugar del global.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from compartido.rutas import MODEL_METADATA, MODEL_REGISTRY
from q2_modelamiento.artefactos import ArtefactoDiferido, ArtefactoNoDisponible

__all__ = [
    "RegistroDeModelos",
    "ArtefactoNoDisponible",
    "registro",
    "cargar_artefacto",
    "metadatos_factores",
    "metadatos_global",
    "medianas_imputacion",
    "inventario",
]


class RegistroDeModelos:
    """Punto unico de acceso a artefactos y metadatos entrenados."""

    def __init__(self, carpeta_artefactos: Path | None = None, carpeta_metadatos: Path | None = None) -> None:
        self.artefactos = carpeta_artefactos or MODEL_REGISTRY
        self.metadatos = carpeta_metadatos or MODEL_METADATA
        self._cache: dict[str, ArtefactoDiferido] = {}

    # -- metadatos ---------------------------------------------------------

    def _leer_json(self, nombre: str) -> dict:
        ruta = self.metadatos / nombre
        if not ruta.exists():
            raise ArtefactoNoDisponible(
                f"No se encontro {nombre} en {self.metadatos}. "
                "Los metadatos SI se versionan en git: revisa models/metadata/."
            )
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)

    def metadatos_factores(self) -> dict[str, Any]:
        return self._leer_json("metadatos_modelos.json")

    def metadatos_global(self) -> dict[str, Any]:
        return self._leer_json("metadatos_modelo_global.json")

    def medianas_imputacion(self) -> dict[str, float]:
        return self._leer_json("medianas_imputacion.json")

    # -- artefactos --------------------------------------------------------

    def obtener(self, nombre_archivo: str) -> ArtefactoDiferido:
        """Devuelve el artefacto SIN deserializarlo todavia."""
        if nombre_archivo not in self._cache:
            self._cache[nombre_archivo] = ArtefactoDiferido(
                self.artefactos / nombre_archivo, etiqueta=nombre_archivo
            )
        return self._cache[nombre_archivo]

    def inventario(self) -> list[dict[str, Any]]:
        if not self.artefactos.exists():
            return []
        try:
            meta_f = self.metadatos_factores()
        except ArtefactoNoDisponible:
            meta_f = {}
        salida = []
        for ruta in sorted(self.artefactos.iterdir()):
            if ruta.suffix not in {".joblib", ".keras"}:
                continue
            codigo = ruta.stem.replace("modelo_", "")
            proxy = self._cache.get(ruta.name)
            salida.append(
                {
                    "archivo": ruta.name,
                    "codigo": codigo,
                    "mb": round(ruta.stat().st_size / 1_048_576, 2),
                    "materializado": bool(proxy and proxy.materializado),
                    "segundos_de_carga": proxy.segundos_de_carga if proxy else None,
                    "metricas": meta_f.get(codigo, {}),
                }
            )
        return salida


@lru_cache(maxsize=1)
def registro() -> RegistroDeModelos:
    """Instancia compartida por proceso. Las pruebas pueden construir la suya."""
    return RegistroDeModelos()


# --- funciones de conveniencia (compatibilidad con el codigo existente) ----

def cargar_artefacto(nombre_archivo: str) -> ArtefactoDiferido:
    return registro().obtener(nombre_archivo)


def metadatos_factores() -> dict[str, Any]:
    return registro().metadatos_factores()


def metadatos_global() -> dict[str, Any]:
    return registro().metadatos_global()


def medianas_imputacion() -> dict[str, float]:
    return registro().medianas_imputacion()


def inventario() -> list[dict[str, Any]]:
    return registro().inventario()
