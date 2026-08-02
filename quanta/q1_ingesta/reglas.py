"""Reglas de cuarentena como especificaciones — CTRL-01.

Cada regla es un objeto con codigo, descripcion y prueba unitaria propia.
El motivo registrado en el reporte de calidad es el codigo de la regla que
rechazo el registro, de modo que el Data Quality Log queda trazable a la norma.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from compartido.especificacion import Especificacion


@dataclass(frozen=True)
class RegistroCandidato:
    """Objeto evaluado por las especificaciones de ingesta."""

    fila: dict
    columna_rbd: str = "rbd"
    columna_anio: str = "anio"
    llaves_vistas: frozenset = frozenset()

    def valor(self, columna: str):
        return self.fila.get(columna)

    @property
    def llave(self) -> tuple:
        return (self.valor(self.columna_rbd), self.valor(self.columna_anio))


def _ausente(valor) -> bool:
    return valor is None or (isinstance(valor, float) and pd.isna(valor)) or valor is pd.NA


class TieneRbdValido(Especificacion[RegistroCandidato]):
    codigo = "rbd_ausente"
    descripcion = "El registro debe declarar un RBD no vacio, leido como texto."

    def es_satisfecha_por(self, c: RegistroCandidato) -> bool:
        v = c.valor(c.columna_rbd)
        return not _ausente(v) and str(v).strip() != ""


class TieneAnioValido(Especificacion[RegistroCandidato]):
    codigo = "anio_ausente"
    descripcion = "El registro debe declarar el periodo que completa la llave RBD + anio."

    def es_satisfecha_por(self, c: RegistroCandidato) -> bool:
        return not _ausente(c.valor(c.columna_anio))


class LlaveEsUnica(Especificacion[RegistroCandidato]):
    codigo = "llave_duplicada"
    descripcion = "La llave compuesta RBD + anio debe ser unica dentro de la fuente."

    def es_satisfecha_por(self, c: RegistroCandidato) -> bool:
        return c.llave not in c.llaves_vistas


class DentroDeVentanaTemporal(Especificacion[RegistroCandidato]):
    """CTRL-02: ningun evento posterior al corte entra al conjunto."""

    codigo = "fuera_de_ventana"
    descripcion = "El evento debe ocurrir dentro de la ventana de medicion declarada."

    def __init__(self, columna_fecha: str, corte: str) -> None:
        self.columna_fecha = columna_fecha
        self.corte = pd.Timestamp(corte)

    def es_satisfecha_por(self, c: RegistroCandidato) -> bool:
        valor = c.valor(self.columna_fecha)
        if _ausente(valor):
            return True
        fecha = pd.to_datetime(valor, errors="coerce")
        return bool(pd.isna(fecha) or fecha <= self.corte)


class FichaInstitucionalRespondida(Especificacion[RegistroCandidato]):
    """Hallazgo del desarrollo: los establecimientos con ficha no respondida
    no son representativos del universo de analisis."""

    codigo = "ficha_no_respondida"
    descripcion = "El establecimiento debe haber respondido la ficha institucional."

    def __init__(self, columna: str = "ficha_no_respondida") -> None:
        self.columna = columna

    def es_satisfecha_por(self, c: RegistroCandidato) -> bool:
        valor = c.valor(self.columna)
        return _ausente(valor) or not bool(valor)


# Conjunto minimo obligatorio para toda fuente.
REGLAS_BASE: tuple[Especificacion[RegistroCandidato], ...] = (
    TieneRbdValido(),
    TieneAnioValido(),
    LlaveEsUnica(),
)
