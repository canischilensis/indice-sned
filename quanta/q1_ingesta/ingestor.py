"""Patron Template Method (Gamma et al., 1994) — esqueleto de ingesta.

El esqueleto es identico para las doce fuentes:

    localizar -> leer -> normalizar la llave -> aplicar cuarentena
              -> escribir parquet -> emitir reporte

Solo varia como se interpreta el archivo concreto. La clase base fija el
esqueleto y los controles CTRL-01/CTRL-02; las subclases solo redefinen los
pasos declarados como ganchos. Una subclase NO PUEDE omitir la validacion de
llave ni la cuarentena: esa es la garantia que un pipeline de datos necesita
frente al antipatron de "jungla de tuberias" (Sculley et al., 2015).

Arquitectonicamente cada paso es un filtro y los checkpoints intermedios en
data/interim son las tuberias materializadas (Pipes and Filters,
Buschmann et al., 1996).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from compartido.especificacion import Especificacion
from compartido.rutas import DATA_PROCESSED, DATA_RAW
from q1_ingesta.calidad import ReporteCalidad, aplicar_cuarentena, leer_tabla, normalizar_rbd
from q1_ingesta.fuentes import Fuente
from q1_ingesta.reglas import REGLAS_BASE


class IngestorDeFuente(ABC):
    """Metodo plantilla de la ingesta. No sobrescribir `ejecutar()`."""

    def __init__(self, fuente: Fuente, reglas: tuple[Especificacion, ...] | None = None) -> None:
        self.fuente = fuente
        self.reglas = reglas if reglas is not None else REGLAS_BASE

    # ---------------- metodo plantilla (invariante) ----------------------

    def ejecutar(self, persistir: bool = True) -> tuple[pd.DataFrame, ReporteCalidad]:
        archivos = self._localizar()
        if not archivos:
            raise FileNotFoundError(
                f"Sin archivos para la fuente '{self.fuente.codigo}' en {self._carpeta()}"
            )

        marcos = [self._leer_archivo(a) for a in archivos]
        crudo = pd.concat(marcos, ignore_index=True)

        crudo = self._normalizar_llave(crudo)
        crudo = self._normalizar(crudo)                       # gancho opcional

        validas, reporte = aplicar_cuarentena(
            crudo,
            fuente=self.fuente.codigo,
            reglas=self.reglas,
            persistir=persistir,
        )

        validas = self._agregar(validas)                      # gancho opcional
        if persistir:
            self._escribir(validas)
        return validas, reporte

    # ---------------- pasos fijos ----------------------------------------

    def _carpeta(self) -> Path:
        return DATA_RAW / self.fuente.carpeta

    def _localizar(self) -> list[Path]:
        carpeta = self._carpeta()
        return sorted(carpeta.glob(self.fuente.patron)) if carpeta.exists() else []

    def _normalizar_llave(self, df: pd.DataFrame) -> pd.DataFrame:
        """CTRL-01: la llave siempre queda como texto y en la columna 'rbd'."""
        for columna in ("rbd", "RBD"):
            if columna in df.columns:
                df = df.rename(columns={columna: "rbd"})
                df["rbd"] = normalizar_rbd(df["rbd"])
                break
        return df

    def _escribir(self, df: pd.DataFrame) -> Path:
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        destino = DATA_PROCESSED / f"{self.fuente.codigo}_por_rbd.parquet"
        df.to_parquet(destino, index=False)
        return destino

    # ---------------- ganchos ---------------------------------------------

    @abstractmethod
    def _leer_archivo(self, ruta: Path) -> pd.DataFrame:
        """Unico paso obligatorio: como se interpreta este formato concreto."""

    def _normalizar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renombres y conversiones propias de la fuente. Opcional."""
        return df

    def _agregar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agregacion a nivel establecimiento-periodo. Opcional."""
        return df


# --------------------------------------------------------------------------
# Adaptadores de lectura (Adapter): una subclase por formato de origen.
# --------------------------------------------------------------------------


class IngestorExcel(IngestorDeFuente):
    """Fuentes publicadas en xls/xlsx (SIMCE, IDPS, IVE, procesos)."""

    hoja: int | str = 0
    filas_a_saltar: int = 0

    def _leer_archivo(self, ruta: Path) -> pd.DataFrame:
        return leer_tabla(ruta, sheet_name=self.hoja, skiprows=self.filas_a_saltar)


class IngestorCsv(IngestorDeFuente):
    """Fuentes publicadas en csv delimitado por punto y coma, latin-1."""

    separador: str = ";"
    codificacion: str = "latin-1"

    def _leer_archivo(self, ruta: Path) -> pd.DataFrame:
        return leer_tabla(ruta, sep=self.separador, encoding=self.codificacion)


class IngestorCsvUtf8(IngestorCsv):
    codificacion = "utf-8"
