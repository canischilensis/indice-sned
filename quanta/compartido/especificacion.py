"""Patron Specification (Evans, 2003; Evans y Fowler, 2002).

Separa el enunciado de un requisito del objeto evaluado. Cada regla de negocio
se convierte en un objeto con nombre, prueba unitaria propia y trazabilidad a la
norma que la origina, en lugar de una rama dentro de una funcion que crece.

Es la respuesta directa al principio CACE (Sculley et al., 2015): cuando el
MINEDUC cambia un criterio se modifica o se agrega una especificacion, y el
resto del flujo no se entera.

Usos implementados: validacion (cuarentena de ingesta) y seleccion (alertas).
Composicion mediante Y / O / NO.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Especificacion(ABC, Generic[T]):
    """Encapsula una prueba booleana sobre un candidato."""

    codigo: str = "sin_codigo"
    descripcion: str = ""

    @abstractmethod
    def es_satisfecha_por(self, candidato: T) -> bool: ...

    # --- combinadores -----------------------------------------------------

    def y(self, otra: Especificacion[T]) -> Especificacion[T]:
        return _Conjuncion(self, otra)

    def o(self, otra: Especificacion[T]) -> Especificacion[T]:
        return _Disyuncion(self, otra)

    def no(self) -> Especificacion[T]:
        return _Negacion(self)

    # azucar sintactico: spec_a & spec_b, spec_a | spec_b, ~spec_a
    __and__ = y
    __or__ = o
    __invert__ = no

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.codigo}>"


class _Conjuncion(Especificacion[T]):
    def __init__(self, izq: Especificacion[T], der: Especificacion[T]) -> None:
        self.izq, self.der = izq, der
        self.codigo = f"({izq.codigo} Y {der.codigo})"

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self.izq.es_satisfecha_por(candidato) and self.der.es_satisfecha_por(candidato)


class _Disyuncion(Especificacion[T]):
    def __init__(self, izq: Especificacion[T], der: Especificacion[T]) -> None:
        self.izq, self.der = izq, der
        self.codigo = f"({izq.codigo} O {der.codigo})"

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self.izq.es_satisfecha_por(candidato) or self.der.es_satisfecha_por(candidato)


class _Negacion(Especificacion[T]):
    def __init__(self, interna: Especificacion[T]) -> None:
        self.interna = interna
        self.codigo = f"NO({interna.codigo})"

    def es_satisfecha_por(self, candidato: T) -> bool:
        return not self.interna.es_satisfecha_por(candidato)


class EspecificacionPredicado(Especificacion[Any]):
    """Adaptador para envolver una funcion existente sin escribir una clase."""

    def __init__(self, codigo: str, predicado, descripcion: str = "") -> None:
        self.codigo = codigo
        self.descripcion = descripcion
        self._predicado = predicado

    def es_satisfecha_por(self, candidato: Any) -> bool:
        return bool(self._predicado(candidato))
