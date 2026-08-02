"""Catalogo de factores del Indice SNED.

Decision de normalizacion 3 (Bloque II): las ponderaciones oficiales son DATO,
no codigo. Una modificacion normativa actualiza este catalogo (y su tabla
espejo en PostgreSQL), no la aplicacion. Mitiga estructuralmente el principio
CACE (Sculley et al., 2015).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from compartido.rutas import CONTRATOS


@dataclass(frozen=True)
class Factor:
    codigo: str
    nombre: str
    peso: float
    r2: float
    mae: float
    restriccion: str | None
    descripcion: str
    es_accionable: bool = True

    @property
    def es_acotado(self) -> bool:
        """True si el factor esta limitado por informacion no publica."""
        return self.restriccion is not None


@lru_cache(maxsize=1)
def cargar_catalogo() -> dict:
    with open(CONTRATOS / "catalogo_factores.json", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def factores() -> dict[str, Factor]:
    datos = cargar_catalogo()["factores"]
    return {
        f["codigo"]: Factor(
            codigo=f["codigo"],
            nombre=f["nombre"],
            peso=f["peso"],
            r2=f["r2"],
            mae=f["mae"],
            restriccion=f.get("restriccion"),
            descripcion=f["descripcion"],
            es_accionable=f.get("es_accionable", True),
        )
        for f in datos
    }


def pesos() -> dict[str, float]:
    return {c: f.peso for c, f in factores().items()}


def reconstruir_indice(valores_factores: dict[str, float]) -> float:
    """Aplica la formula oficial: suma ponderada de los seis factores.

    Verificada empiricamente contra el indice ministerial con R2 = 1.0000
    y MAE = 0.000 (Informe tecnico, seccion 7.7).
    """
    p = pesos()
    faltantes = set(p) - set(valores_factores)
    if faltantes:
        raise ValueError(f"Faltan factores para reconstruir el indice: {sorted(faltantes)}")
    return float(sum(valores_factores[c] * peso for c, peso in p.items()))


def verificar_suma_pesos(tolerancia: float = 1e-9) -> None:
    total = sum(pesos().values())
    if abs(total - 1.0) > tolerancia:
        raise ValueError(f"Las ponderaciones del catalogo suman {total}, se esperaba 1.0")
