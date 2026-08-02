"""Contratos de entrada y salida del servicio (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ObservacionEntrada(BaseModel):
    """Variables de gestion de un establecimiento-periodo."""

    model_config = ConfigDict(extra="allow")

    rbd: str = Field(..., description="Rol Base de Datos, como texto (conserva ceros a la izquierda)")
    periodo: str | None = Field(None, description="Bienio de premiacion, ej. '2024-2025'")
    variables: dict[str, float | None] = Field(default_factory=dict)


class FactorPredicho(BaseModel):
    codigo: str
    nombre: str
    peso: float
    valor: float
    aporte_al_indice: float
    es_acotado: bool
    restriccion: str | None = None


class RespuestaPrediccion(BaseModel):
    rbd: str
    indice: float
    factores: list[FactorPredicho] = []
    estrategia: str
    version_modelo: str
    incertidumbre_mae: float | None = None
    advertencia: str


class ContribucionSalida(BaseModel):
    variable: str
    etiqueta: str
    valor: float | None
    contribucion: float
    direccion: str


class RespuestaExplicacion(BaseModel):
    rbd: str
    factor: str
    prediccion: float
    valor_base: float
    aditividad_verificada: bool
    contribuciones: list[ContribucionSalida]
    lectura: str


class SolicitudSimulacion(BaseModel):
    rbd: str
    variable: str
    rango: list[float] | None = None
    n_puntos: int = Field(25, ge=5, le=100)
    variables: dict[str, float | None] = Field(default_factory=dict)


class RespuestaSimulacion(BaseModel):
    rbd: str
    variable: str
    etiqueta: str
    valores: list[float]
    predicciones: list[float]
    valor_actual: float | None
    prediccion_actual: float | None
    monotona: bool
    advertencia_magnitud: str


class Alerta(BaseModel):
    tipo: str
    severidad: str
    titulo: str
    detalle: str


class RespuestaAlertas(BaseModel):
    rbd: str
    alertas: list[Alerta]
