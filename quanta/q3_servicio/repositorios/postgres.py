"""Adaptador de produccion: reconstruye la observacion desde PostgreSQL.

El adaptador es responsable de entregar EL MISMO objeto de dominio que el de
parquet: misma nomenclatura de variables y mismos nulos. Que la fuente sea
normalizada en formato largo es asunto suyo, no de la capa de servicio.

Nota sobre el RBD: en el esquema fisico es INTEGER, su forma canonica. La
ingesta lo lee como texto para no perder ceros a la izquierda durante el
parseo; aqui llega normalizado y se convierte al consultar.
"""

from __future__ import annotations

from q3_servicio.repositorios.contrato import (
    ConjuntoNoDisponible,
    EstablecimientoNoEncontrado,
    RepositorioEstablecimientos,
)

# Reconstruye la representacion ancha desde las tablas normalizadas.
# Los alias replican la nomenclatura del conjunto de entrenamiento.
CONSULTA_DETALLE = """
WITH ciclo AS (
    SELECT sr.rbd, sr.periodo_id, p.etiqueta, sr.cluster_codigo, sr.indicer, sr.sel,
           ep.cod_depe2, ep.es_rural, e.nombre
    FROM hechos.sned_resultado sr
    JOIN core.periodo p ON p.periodo_id = sr.periodo_id AND p.tipo = 'CICLO_SNED'
    JOIN core.establecimiento e ON e.rbd = sr.rbd
    LEFT JOIN core.establecimiento_periodo ep
           ON ep.rbd = sr.rbd AND ep.periodo_id = sr.periodo_id
    WHERE sr.rbd = :rbd
      AND (CAST(:ciclo AS text) IS NULL OR p.etiqueta = CAST(:ciclo AS text))
    ORDER BY p.anio_inicio DESC
    LIMIT 1
),
med AS (SELECT periodo_id FROM core.periodo WHERE tipo='BIENIO_MEDICION' AND etiqueta='2018-19'),
simce AS (
    SELECT s.rbd,
      MAX(puntaje) FILTER (WHERE nivel_cod='4b' AND asignatura_cod='LECT') AS simce_lect_4b,
      MAX(puntaje) FILTER (WHERE nivel_cod='4b' AND asignatura_cod='MATE') AS simce_mate_4b,
      MAX(puntaje) FILTER (WHERE nivel_cod='6b' AND asignatura_cod='LECT') AS simce_lect_6b,
      MAX(puntaje) FILTER (WHERE nivel_cod='6b' AND asignatura_cod='MATE') AS simce_mate_6b,
      MAX(puntaje) FILTER (WHERE nivel_cod='8b' AND asignatura_cod='LECT') AS simce_lect_8b,
      MAX(puntaje) FILTER (WHERE nivel_cod='8b' AND asignatura_cod='MATE') AS simce_mate_8b,
      MAX(puntaje) FILTER (WHERE nivel_cod='2m' AND asignatura_cod='LECT') AS simce_lect_2m,
      MAX(puntaje) FILTER (WHERE nivel_cod='2m' AND asignatura_cod='MATE') AS simce_mate_2m
    FROM hechos.simce_medicion s, med WHERE s.rbd=:rbd AND s.periodo_id=med.periodo_id GROUP BY s.rbd
),
idps AS (
    SELECT i.rbd,
      MAX(valor) FILTER (WHERE nivel_cod='4b' AND dimension_cod='AM') AS idps_am_4b,
      MAX(valor) FILTER (WHERE nivel_cod='4b' AND dimension_cod='CC') AS idps_cc_4b,
      MAX(valor) FILTER (WHERE nivel_cod='4b' AND dimension_cod='PF') AS idps_pf_4b,
      MAX(valor) FILTER (WHERE nivel_cod='4b' AND dimension_cod='HV') AS idps_hv_4b,
      MAX(valor) FILTER (WHERE nivel_cod='6b' AND dimension_cod='AM') AS idps_am_6b,
      MAX(valor) FILTER (WHERE nivel_cod='6b' AND dimension_cod='CC') AS idps_cc_6b,
      MAX(valor) FILTER (WHERE nivel_cod='6b' AND dimension_cod='PF') AS idps_pf_6b,
      MAX(valor) FILTER (WHERE nivel_cod='6b' AND dimension_cod='HV') AS idps_hv_6b,
      MAX(valor) FILTER (WHERE nivel_cod='8b' AND dimension_cod='AM') AS idps_am_8b,
      MAX(valor) FILTER (WHERE nivel_cod='8b' AND dimension_cod='CC') AS idps_cc_8b,
      MAX(valor) FILTER (WHERE nivel_cod='8b' AND dimension_cod='PF') AS idps_pf_8b,
      MAX(valor) FILTER (WHERE nivel_cod='8b' AND dimension_cod='HV') AS idps_hv_8b,
      MAX(valor) FILTER (WHERE nivel_cod='2m' AND dimension_cod='AM') AS idps_am_2m,
      MAX(valor) FILTER (WHERE nivel_cod='2m' AND dimension_cod='CC') AS idps_cc_2m,
      MAX(valor) FILTER (WHERE nivel_cod='2m' AND dimension_cod='PF') AS idps_pf_2m,
      MAX(valor) FILTER (WHERE nivel_cod='2m' AND dimension_cod='HV') AS idps_hv_2m
    FROM hechos.idps_medicion i, med WHERE i.rbd=:rbd AND i.periodo_id=med.periodo_id GROUP BY i.rbd
),
ind AS (
    SELECT a.rbd,
      MAX(valor) FILTER (WHERE indicador_cod='TASA_APROBACION')  AS tasa_aprobacion,
      MAX(valor) FILTER (WHERE indicador_cod='TASA_REPROBACION') AS tasa_reprobacion,
      MAX(valor) FILTER (WHERE indicador_cod='TASA_RETIRO')      AS tasa_retiro,
      MAX(valor) FILTER (WHERE indicador_cod='MATRICULA_TOTAL')  AS matricula_total,
      MAX(valor) FILTER (WHERE indicador_cod='MATRICULA_REND')   AS total_matricula,
      MAX(valor) FILTER (WHERE indicador_cod='CURSOS_TOTAL')     AS cursos_total,
      MAX(valor) FILTER (WHERE indicador_cod='N_VULNERABLES')    AS n_vulnerables,
      MAX(valor) FILTER (WHERE indicador_cod='N_BENEF_SEP')      AS n_beneficiarios_sep,
      MAX(valor) FILTER (WHERE indicador_cod='CONVENIO_SEP')     AS tiene_convenio_sep,
      MAX(valor) FILTER (WHERE indicador_cod='N_DOCENTES')       AS n_docentes,
      MAX(valor) FILTER (WHERE indicador_cod='HORAS_DOCENTES')   AS horas_docentes,
      MAX(valor) FILTER (WHERE indicador_cod='N_DIRECTIVOS')     AS n_directivos,
      MAX(valor) FILTER (WHERE indicador_cod='N_ASISTENTES')     AS n_asistentes,
      MAX(valor) FILTER (WHERE indicador_cod='IVE_BASICA')       AS ive_basica,
      MAX(valor) FILTER (WHERE indicador_cod='IVE_MEDIA')        AS ive_media,
      MAX(valor) FILTER (WHERE indicador_cod='IVE_CONSOLIDADO')  AS ive_consolidado
    FROM hechos.indicador_anual a, med WHERE a.rbd=:rbd AND a.periodo_id=med.periodo_id GROUP BY a.rbd
),
sie AS (
    -- La ausencia de fila significa CERO eventos registrados, no dato
    -- desconocido: un establecimiento sin denuncias tiene cero denuncias.
    SELECT v.rbd,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='DEN_TOTAL'), 0)    AS denuncias_total,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='DEN_FISC'), 0)     AS denuncias_fiscalizacion,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='DEN_JURID'), 0)    AS denuncias_juridica,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='DEN_CIBER'), 0)    AS denuncias_ciberbullying,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='PA_TOTAL'), 0)     AS procesos_total,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='PA_SANCION'), 0)   AS procesos_con_sancion,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='PA_MULTA'), 0)     AS procesos_multa,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='PA_PRIVACION'), 0) AS procesos_privacion_subvencion,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='MED_TOTAL'), 0)    AS mediaciones_total,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='MED_EFECTIVA'), 0) AS mediaciones_efectivas,
      COALESCE(MAX(conteo) FILTER (WHERE tipo_evento_cod='MED_DE_DENUNCIA'), 0) AS mediaciones_de_denuncia
    FROM hechos.sie_evento_agregado v
    JOIN core.ventana_sie w ON w.ventana_id=v.ventana_id AND w.proposito='ENTRENAMIENTO'
    WHERE v.rbd=:rbd GROUP BY v.rbd
)
SELECT c.rbd, c.etiqueta AS "BIENIO_PREMIO", c.cluster_codigo AS "CLUSTER",
       c.indicer AS "INDICER", c.sel AS "SEL", c.cod_depe2, c.es_rural AS "ES_RURAL",
       c.nombre AS nom_rbd,
       simce.*, idps.*, ind.*,
       COALESCE(sie.denuncias_total, 0) AS denuncias_total,
       COALESCE(sie.denuncias_fiscalizacion, 0) AS denuncias_fiscalizacion,
       COALESCE(sie.denuncias_juridica, 0) AS denuncias_juridica,
       COALESCE(sie.denuncias_ciberbullying, 0) AS denuncias_ciberbullying,
       COALESCE(sie.procesos_total, 0) AS procesos_total,
       COALESCE(sie.procesos_con_sancion, 0) AS procesos_con_sancion,
       COALESCE(sie.procesos_multa, 0) AS procesos_multa,
       COALESCE(sie.procesos_privacion_subvencion, 0) AS procesos_privacion_subvencion,
       COALESCE(sie.mediaciones_total, 0) AS mediaciones_total,
       COALESCE(sie.mediaciones_efectivas, 0) AS mediaciones_efectivas,
       COALESCE(sie.mediaciones_de_denuncia, 0) AS mediaciones_de_denuncia
FROM ciclo c
LEFT JOIN simce ON TRUE LEFT JOIN idps ON TRUE LEFT JOIN ind ON TRUE LEFT JOIN sie ON TRUE
"""

# DISTINCT ON entrega UN registro por establecimiento, el del ciclo mas
# reciente. Sin el, un RBD con cinco ciclos consumiria cinco cupos del limite y
# el listado no coincidiria con el del adaptador de parquet.
CONSULTA_LISTADO = """
    SELECT * FROM (
        SELECT DISTINCT ON (sr.rbd)
               sr.rbd, p.etiqueta AS bienio_premio, sr.cluster_codigo, sr.indicer
        FROM hechos.sned_resultado sr
        JOIN core.periodo p ON p.periodo_id = sr.periodo_id AND p.tipo='CICLO_SNED'
        WHERE sr.rbd = ANY(:rbds)
        ORDER BY sr.rbd, p.anio_inicio DESC
    ) t
    ORDER BY rbd
    LIMIT :limite
"""

CONSULTA_RANKING = """
    SELECT r.rbd, p.etiqueta AS ciclo, r.cluster_codigo, r.indicer,
           r.posicion_en_grupo, r.n_grupo, ROUND(r.percentil::numeric, 4) AS percentil, r.sel
    FROM hechos.v_ranking_intra_cluster r
    JOIN core.periodo p ON p.periodo_id = r.periodo_id AND p.tipo='CICLO_SNED'
    WHERE r.rbd = :rbd AND (CAST(:ciclo AS text) IS NULL OR p.etiqueta = CAST(:ciclo AS text))
    ORDER BY p.anio_inicio DESC
    LIMIT 1
"""

CONSULTA_RBD_MUESTRA = "SELECT rbd FROM core.conjunto_entrenamiento ORDER BY rbd LIMIT 1"


class RepositorioPostgres(RepositorioEstablecimientos):
    origen = "postgres"

    def __init__(self, url: str | None = None) -> None:
        self._url = url
        self._motor = None
        self._columnas: set[str] | None = None

    def _conectar(self):
        if self._motor is None:
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:  # pragma: no cover
                raise ConjuntoNoDisponible("SQLAlchemy no esta instalado.") from exc
            import os

            # Orden de resolucion: inyeccion explicita, entorno del proceso y,
            # por ultimo, la configuracion de la aplicacion, que es la unica que
            # lee el archivo .env. Sin ese tercer paso el adaptador solo funciona
            # si alguien exporto la variable a mano en la terminal.
            url = self._url or os.getenv("DATABASE_URL")
            if not url:
                from q3_servicio.core.config import config

                url = config().database_url
            if not url or "cambiar-en-local" in url:
                raise ConjuntoNoDisponible(
                    "Falta DATABASE_URL: definala en el archivo .env de la raiz del "
                    "repositorio o exportela como variable de entorno."
                )
            self._motor = create_engine(url, future=True)
        return self._motor

    @staticmethod
    def _como_entero(rbd: str) -> int:
        try:
            return int(str(rbd).strip().lstrip("0") or "0")
        except ValueError as exc:
            raise EstablecimientoNoEncontrado(f"RBD no numerico: {rbd!r}") from exc

    def obtener(self, rbd: str, periodo: str | None = None) -> dict:
        from sqlalchemy import text

        with self._conectar().connect() as cx:
            fila = cx.execute(text(CONSULTA_DETALLE),
                              {"rbd": self._como_entero(rbd), "ciclo": periodo}).mappings().first()
        if fila is None:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin registros en la base analitica.")
        d = {k: v for k, v in dict(fila).items() if k != "rbd"}
        d["rbd"] = str(self._como_entero(rbd))
        return {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in d.items()}

    def listar(self, rbds: list[str], limite: int = 50) -> list[dict]:
        from sqlalchemy import text

        with self._conectar().connect() as cx:
            filas = cx.execute(text(CONSULTA_LISTADO),
                               {"rbds": [self._como_entero(r) for r in rbds],
                                "limite": limite}).mappings().all()
        return [
            {
                "rbd": str(f["rbd"]),
                "bienio_premio": f["bienio_premio"],
                "cluster_codigo": f["cluster_codigo"],
                "indicer": float(f["indicer"]) if f["indicer"] is not None else None,
            }
            for f in filas
        ]

    def ranking(self, rbd: str, periodo: str | None = None) -> dict:
        from sqlalchemy import text

        with self._conectar().connect() as cx:
            f = cx.execute(text(CONSULTA_RANKING),
                           {"rbd": self._como_entero(rbd), "ciclo": periodo}).mappings().first()
        if f is None:
            raise EstablecimientoNoEncontrado(f"RBD {rbd} sin ranking calculable.")
        d = {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in dict(f).items()}
        d["rbd"] = str(d["rbd"])
        return d

    def variables_disponibles(self) -> set[str]:
        """Las variables que este adaptador entrega de verdad.

        Se obtienen de una observacion real, no del catalogo de columnas de la
        vista materializada: la consulta reconstruye la representacion ancha
        desde varias tablas y la vista no la refleja.
        """
        if self._columnas is None:
            from sqlalchemy import text

            try:
                with self._conectar().connect() as cx:
                    rbd = cx.execute(text(CONSULTA_RBD_MUESTRA)).scalar()
                self._columnas = set(self.obtener(str(rbd))) if rbd is not None else set()
            except Exception:
                self._columnas = set()
        return self._columnas

    def existe(self, rbd: str) -> bool:
        try:
            self.obtener(rbd)
            return True
        except EstablecimientoNoEncontrado:
            return False
