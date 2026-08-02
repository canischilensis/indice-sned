"""Inventario declarativo de las fuentes publicas integradas (OE1).

Anadir una fuente = agregar una entrada aqui. Decision de normalizacion 6:
los indicadores anuales de contexto se unifican en una tabla generica con
catalogo de tipos, de modo que incorporar una fuente inserta registros y no
altera el esquema.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    codigo: str
    nombre: str
    organismo: str
    carpeta: str
    patron: str
    llave: tuple[str, ...]
    periodicidad: str
    notas: str = ""


FUENTES: tuple[Fuente, ...] = (
    Fuente("simce", "Mediciones estandarizadas SIMCE", "Agencia de Calidad",
           "simce", "simce*_rbd*.xls*", ("rbd", "anio", "nivel", "asignatura"), "anual",
           "Se excluye 2022 por retiro de consecuencias (excepcion normativa postpandemia)."),
    Fuente("idps", "Indicadores de Desarrollo Personal y Social", "Agencia de Calidad",
           "idps", "idps*_rbd*.xls*", ("rbd", "anio", "nivel"), "anual",
           "Cuatro dimensiones: autoestima, convivencia, participacion, vida saludable."),
    Fuente("sned", "Resultados oficiales del Indice SNED", "MINEDUC",
           "sned", "SNED_*.csv", ("rbd", "bienio"), "bianual",
           "Contiene INDICER, los seis factores, CLUSTER y SEL. Fuente de la variable objetivo."),
    Fuente("rendimiento", "Resumen de rendimiento por establecimiento", "MINEDUC",
           "rendimiento", "*Rendimiento*.csv", ("rbd", "anio"), "anual",
           "Publicado sin clasificacion previa: requiere normalizacion (OE2)."),
    Fuente("matricula", "Resumen de matricula por unidad educativa", "MINEDUC",
           "matricula", "*matricula*.csv", ("rbd", "anio"), "anual"),
    Fuente("sep", "Preferentes, prioritarios y beneficiarios SEP", "MINEDUC",
           "sep", "*SEP*.csv", ("rbd", "anio"), "anual"),
    Fuente("ive", "Indice de Vulnerabilidad Escolar", "JUNAEB",
           "ive", "*IVE*.xlsx", ("rbd", "anio"), "anual"),
    Fuente("personal", "Dotacion docente y asistentes de la educacion", "MINEDUC",
           "personal", "*.csv", ("rbd", "anio"), "anual"),
    Fuente("pat", "Procesos administrativos", "Superintendencia de Educacion",
           "pat", "PAT*.xlsx", ("rbd", "anio"), "anual",
           "Ventana temporal declarada explicitamente (decision de normalizacion 5)."),
    Fuente("denuncias", "Denuncias ciudadanas", "Superintendencia de Educacion",
           "denuncias", "DENUNCIAS_*.csv", ("rbd", "anio"), "anual"),
    Fuente("mediaciones", "Mediaciones escolares", "Superintendencia de Educacion",
           "mediaciones", "*MEDIACIONES*.csv", ("rbd", "anio"), "anual"),
    Fuente("desvinculacion", "Tasa de incidencia de desvinculacion", "MINEDUC",
           "desvinculacion", "*Desvinculacion*.xlsx", ("rbd", "anio"), "anual"),
)


def por_codigo(codigo: str) -> Fuente:
    for f in FUENTES:
        if f.codigo == codigo:
            return f
    raise KeyError(f"Fuente desconocida: {codigo}. Disponibles: {[f.codigo for f in FUENTES]}")
