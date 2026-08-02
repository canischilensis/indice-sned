"""Traduccion de nombres tecnicos de variables a lenguaje de gestion escolar.

La brecha entre disponibilidad del dato y su comprension por usuarios no
expertos (Taut et al., 2009) se cierra aqui, no en el frontend: asi el
diccionario es unico y auditable.
"""

from __future__ import annotations

_NIVEL = {"4b": "4to basico", "6b": "6to basico", "8b": "8vo basico", "2m": "2do medio"}
_IDPS = {
    "am": "Autoestima academica",
    "cc": "Clima de convivencia",
    "pf": "Participacion y formacion ciudadana",
    "hv": "Habitos de vida saludable",
}

_EXPLICITAS = {
    "tasa_aprobacion": "Tasa de aprobacion",
    "tasa_reprobacion": "Tasa de reprobacion",
    "tasa_retiro": "Tasa de retiro",
    "matricula_total": "Matricula total",
    "total_matricula": "Matricula total (resumen)",
    "cursos_total": "Cursos totales",
    "n_vulnerables": "Estudiantes vulnerables",
    "n_beneficiarios_sep": "Beneficiarios SEP",
    "tiene_convenio_sep": "Convenio SEP vigente",
    "ive_basica": "IVE basica",
    "ive_media": "IVE media",
    "ive_consolidado": "IVE consolidado",
    "n_docentes": "Dotacion docente",
    "horas_docentes": "Horas docentes contratadas",
    "n_directivos": "Equipo directivo",
    "n_asistentes": "Asistentes de la educacion",
    "denuncias_total": "Denuncias totales",
    "denuncias_juridica": "Denuncias con derivacion juridica",
    "denuncias_fiscalizacion": "Denuncias con fiscalizacion",
    "denuncias_ciberbullying": "Denuncias por ciberacoso",
    "procesos_total": "Procesos administrativos",
    "procesos_con_sancion": "Procesos con sancion",
    "procesos_multa": "Procesos con multa",
    "procesos_privacion_subvencion": "Procesos con privacion de subvencion",
    "mediaciones_total": "Mediaciones",
    "mediaciones_efectivas": "Mediaciones efectivas",
    "mediaciones_de_denuncia": "Mediaciones originadas en denuncia",
    "ficha_no_respondida": "Ficha institucional no respondida",
    "CLUSTER": "Grupo homogeneo oficial",
    "cod_depe2": "Dependencia administrativa",
    "ES_RURAL": "Ruralidad",
    "BIENIO_PREMIO": "Bienio de premiacion",
}


def etiqueta_de(variable: str) -> str:
    if variable in _EXPLICITAS:
        return _EXPLICITAS[variable]

    partes = variable.split("_")
    if variable.startswith("dif_simce_"):
        _, _, asignatura, nivel = partes
        materia = "Lectura" if asignatura == "lect" else "Matematica"
        return f"Variacion SIMCE {materia} {_NIVEL.get(nivel, nivel)}"
    if variable.startswith("simce_prom_"):
        return f"Promedio SIMCE {_NIVEL.get(partes[-1], partes[-1])}"
    if variable.startswith("simce_"):
        _, asignatura, nivel = partes
        materia = "Lectura" if asignatura == "lect" else "Matematica"
        return f"SIMCE {materia} {_NIVEL.get(nivel, nivel)}"
    if variable.startswith("idps_"):
        _, dimension, nivel = partes
        return f"IDPS {_IDPS.get(dimension, dimension)} {_NIVEL.get(nivel, nivel)}"
    return variable.replace("_", " ").capitalize()
