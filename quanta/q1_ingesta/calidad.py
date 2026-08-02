"""Controles de calidad de la ingesta — CTRL-01.

Tres invariantes que ningun dato cruza sin cumplir:
  1. El RBD se lee SIEMPRE como texto. Leerlo como entero destruye los ceros
     a la izquierda y rompe silenciosamente el cruce entre fuentes.
  2. La llave compuesta RBD + anio debe ser valida y unica por fuente.
  3. Lo que no cruza no se elimina: se aisla en cuarentena con bandera de
     auditoria, conservando la trazabilidad de la exclusion.

Las reglas concretas viven en `reglas.py` como especificaciones componibles
(Evans, 2003). Este modulo solo orquesta su aplicacion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from compartido.especificacion import Especificacion
from compartido.rutas import DATA_INTERIM
from q1_ingesta.reglas import REGLAS_BASE, RegistroCandidato


@dataclass
class ReporteCalidad:
    """Data Quality Log: evidencia de CTRL-01."""

    fuente: str
    filas_leidas: int = 0
    filas_validas: int = 0
    filas_cuarentena: int = 0
    motivos: dict[str, int] = field(default_factory=dict)
    reglas_aplicadas: list[str] = field(default_factory=list)

    @property
    def cobertura_llave(self) -> float:
        return 0.0 if not self.filas_leidas else self.filas_validas / self.filas_leidas

    def cumple_umbral(self, umbral: float = 0.95) -> bool:
        """Meta declarada en la Tabla N.5 del proyecto: cobertura >= 95 %."""
        return self.cobertura_llave >= umbral

    def resumen(self) -> str:
        return (
            f"[{self.fuente}] leidas={self.filas_leidas} validas={self.filas_validas} "
            f"cuarentena={self.filas_cuarentena} cobertura={self.cobertura_llave:.2%} "
            f"{'OK' if self.cumple_umbral() else 'BAJO UMBRAL'}"
        )


DTYPE_LLAVE = {"RBD": "string", "rbd": "string"}


def leer_tabla(ruta: Path, **kwargs) -> pd.DataFrame:
    """Lectura blindada: el identificador nunca se infiere como numero."""
    dtype = {**DTYPE_LLAVE, **kwargs.pop("dtype", {})}
    if ruta.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(ruta, dtype=dtype, **kwargs)
    sep = kwargs.pop("sep", ";")
    encoding = kwargs.pop("encoding", "latin-1")
    return pd.read_csv(ruta, dtype=dtype, sep=sep, encoding=encoding, low_memory=False, **kwargs)


def normalizar_rbd(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.strip().str.lstrip("0").replace({"": pd.NA})


def aplicar_cuarentena(
    df: pd.DataFrame,
    fuente: str,
    columna_rbd: str = "rbd",
    columna_anio: str = "anio",
    reglas: tuple[Especificacion, ...] | None = None,
    persistir: bool = True,
) -> tuple[pd.DataFrame, ReporteCalidad]:
    """Separa el conjunto valido del cuarentenado. Nada se borra.

    Cada fila se evalua contra las especificaciones en orden; la primera que
    falla determina el motivo registrado, que es el codigo de esa regla.
    """
    reglas = reglas if reglas is not None else REGLAS_BASE
    reporte = ReporteCalidad(
        fuente=fuente,
        filas_leidas=len(df),
        reglas_aplicadas=[r.codigo for r in reglas],
    )

    motivos: list[str | None] = []
    llaves_vistas: set[tuple] = set()

    for fila in df.to_dict(orient="records"):
        candidato = RegistroCandidato(
            fila=fila,
            columna_rbd=columna_rbd,
            columna_anio=columna_anio,
            llaves_vistas=frozenset(llaves_vistas),
        )
        motivo = next(
            (r.codigo for r in reglas if not r.es_satisfecha_por(candidato)),
            None,
        )
        motivos.append(motivo)
        if motivo is None:
            llaves_vistas.add(candidato.llave)

    trabajo = df.copy()
    trabajo["_motivo_cuarentena"] = pd.array(motivos, dtype="string")

    cuarentena = trabajo[trabajo["_motivo_cuarentena"].notna()]
    validas = trabajo[trabajo["_motivo_cuarentena"].isna()].drop(columns=["_motivo_cuarentena"])

    reporte.filas_validas = len(validas)
    reporte.filas_cuarentena = len(cuarentena)
    reporte.motivos = cuarentena["_motivo_cuarentena"].value_counts().to_dict()

    if persistir and len(cuarentena):
        destino = DATA_INTERIM / "cuarentena"
        destino.mkdir(parents=True, exist_ok=True)
        cuarentena.to_parquet(destino / f"{fuente}_cuarentena.parquet", index=False)

    return validas, reporte


def verificar_ventana_temporal(df: pd.DataFrame, columna_fecha: str, corte: str) -> pd.DataFrame:
    """Regla anti-fuga temporal. Conservada por compatibilidad; la forma
    preferida es componer `DentroDeVentanaTemporal` en las reglas de cuarentena."""
    fechas = pd.to_datetime(df[columna_fecha], errors="coerce")
    return df[fechas <= pd.Timestamp(corte)]
