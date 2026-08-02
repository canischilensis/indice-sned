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
# Las once columnas de eventos SIE. El merge original fue LEFT y dejo nulos
# donde no hubo evento; un establecimiento sin denuncias registradas tiene CERO
# denuncias, no un dato desconocido. La base ya carga 0 desde los parquet
# originales, de modo que aqui se normaliza para que ambos adaptadores
# devuelvan lo mismo.
EVENTOS_SIE = (
    "denuncias_total", "denuncias_fiscalizacion", "denuncias_juridica",
    "denuncias_ciberbullying", "procesos_total", "procesos_con_sancion",
    "procesos_multa", "procesos_privacion_subvencion",
    "mediaciones_total", "mediaciones_efectivas", "mediaciones_de_denuncia",
)

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
                for c in EVENTOS_SIE:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
                if "cod_depe2" in df.columns:
                    # Sin traduccion de codigos: la diferencia con PostgreSQL es
                    # temporal, no de vocabulario. Ver la nota en la prueba de
                    # paridad.
                    df["cod_depe2"] = pd.to_numeric(df["cod_depe2"], errors="coerce")
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

    def ranking(self, rbd: str, periodo: str | None = None) -> dict:
        """Ranking calculado en memoria sobre el conjunto cargado."""
        df = self._conjunto()
        fila = self.obtener(rbd, periodo)
        ciclo = fila.get("BIENIO_PREMIO")
        cluster = fila.get("CLUSTER")
        if ciclo is None or cluster is None or "INDICER" not in df.columns:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin ranking calculable.")

        grupo = df[(df["BIENIO_PREMIO"] == ciclo) & (df["CLUSTER"] == cluster)]
        grupo = grupo[grupo["INDICER"].notna()].sort_values("INDICER", ascending=False)
        orden = grupo["rbd"].tolist()
        n = len(orden)
        pos = orden.index(str(rbd).strip()) + 1
        return {
            "rbd": str(rbd).strip(),
            "ciclo": str(ciclo),
            "cluster_codigo": int(cluster),
            "indicer": float(fila["INDICER"]),
            "posicion_en_grupo": pos,
            "n_grupo": n,
            "percentil": round((n - pos) / (n - 1), 4) if n > 1 else 0.0,
            "sel": int(fila["SEL"]) if fila.get("SEL") is not None else None,
        }
