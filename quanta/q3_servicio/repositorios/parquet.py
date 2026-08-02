"""Adaptador de desarrollo: lee el parquet producido por el cuanto 1.

Permite que el prototipo funcione sin PostgreSQL levantado, que es la condicion
para demostrarlo en una defensa sin depender de Docker.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from compartido.rutas import DATA_PROCESSED
from q3_servicio.repositorios.contrato import (
    ConjuntoNoDisponible,
    EstablecimientoNoEncontrado,
    RepositorioEstablecimientos,
)

# Orden deliberado: primero la tabla que reproduce la representacion de
# entrenamiento (23.111 observaciones, la misma cifra que declara
# metadatos_modelo_global.json). Las restantes son respaldos historicos con
# menos variables y sirven solo para que el prototipo no quede inoperante.
CANDIDATOS = (
    "tabla_modelo_largo.parquet",
    "tabla_modelo_final.parquet",
    "tabla_entrenamiento_completa.parquet",
    "tabla_entrenamiento_modelo.parquet",
)


class RepositorioParquet(RepositorioEstablecimientos):
    origen = "parquet"

    def __init__(self, carpeta=None, candidatos: tuple[str, ...] = CANDIDATOS) -> None:
        self._carpeta = carpeta or DATA_PROCESSED
        self._candidatos = candidatos

    @lru_cache(maxsize=4)  # noqa: B019 - instancia unica por proceso
    def _conjunto(self) -> pd.DataFrame:
        for nombre in self._candidatos:
            ruta = self._carpeta / nombre
            if ruta.exists():
                df = pd.read_parquet(ruta)
                for col in df.columns:
                    if col.lower() == "rbd":
                        df["rbd"] = df[col].astype("string").str.strip()
                        break
                return df
        raise ConjuntoNoDisponible(
            f"No se encontro ningun conjunto en {self._carpeta}. "
            "Ejecuta los notebooks 01_ y 02_ o restaura data/processed."
        )

    def obtener(self, rbd: str, periodo: str | None = None) -> dict:
        df = self._conjunto()
        filas = df[df["rbd"] == str(rbd).strip()]
        if filas.empty:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin registros en el conjunto analitico.")
        if periodo and "BIENIO_PREMIO" in filas.columns:
            candidatas = filas[filas["BIENIO_PREMIO"].astype("string") == periodo]
            if not candidatas.empty:
                filas = candidatas
        fila = filas.iloc[-1]
        return {k: (None if pd.isna(v) else v) for k, v in fila.to_dict().items()}

    def listar(self, rbds: list[str], limite: int = 50) -> list[dict]:
        df = self._conjunto()
        subset = df[df["rbd"].isin([str(r) for r in rbds])].head(limite)
        columnas = [c for c in ("rbd", "BIENIO_PREMIO", "CLUSTER", "INDICER", "SEL") if c in subset.columns]
        return subset[columnas].to_dict(orient="records") if columnas else []

    def variables_disponibles(self) -> set[str]:
        """Columnas efectivamente presentes en el conjunto activo."""
        try:
            return set(self._conjunto().columns)
        except ConjuntoNoDisponible:
            return set()

    def existe(self, rbd: str) -> bool:
        try:
            return not self._conjunto()[self._conjunto()["rbd"] == str(rbd).strip()].empty
        except ConjuntoNoDisponible:
            return False
