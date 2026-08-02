-- ===========================================================================
-- Vista 3 · Matriz de entrenamiento (MATERIALIZADA)
-- ---------------------------------------------------------------------------
-- Deshace el formato largo y reconstruye la representacion ancha que exigen
-- los algoritmos. Es el unico objeto materializado del esquema, por dos
-- razones: el pivote es costoso y los datos son estaticos bajo el esquema de
-- reentrenamiento bianual.
--
-- Refrescar SOLO tras cada publicacion del MINEDUC:
--     REFRESH MATERIALIZED VIEW CONCURRENTLY ml.mv_matriz_entrenamiento;
-- ===========================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS ml.mv_matriz_entrenamiento AS
SELECT
    r.rbd,
    r.periodo_id,
    p.etiqueta        AS bienio_premio,
    r.cluster_codigo,
    r.indicer,
    ep.cod_depe2,
    ep.es_rural,

    -- SIMCE: cuatro niveles x dos asignaturas
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='4b' AND s.asignatura_cod='lect') AS simce_lect_4b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='4b' AND s.asignatura_cod='mate') AS simce_mate_4b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='6b' AND s.asignatura_cod='lect') AS simce_lect_6b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='6b' AND s.asignatura_cod='mate') AS simce_mate_6b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='8b' AND s.asignatura_cod='lect') AS simce_lect_8b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='8b' AND s.asignatura_cod='mate') AS simce_mate_8b,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='2m' AND s.asignatura_cod='lect') AS simce_lect_2m,
    MAX(s.puntaje) FILTER (WHERE s.nivel_cod='2m' AND s.asignatura_cod='mate') AS simce_mate_2m,

    -- IDPS: cuatro dimensiones en 4to basico
    MAX(i.valor) FILTER (WHERE i.nivel_cod='4b' AND i.dimension_cod='am') AS idps_am_4b,
    MAX(i.valor) FILTER (WHERE i.nivel_cod='4b' AND i.dimension_cod='cc') AS idps_cc_4b,
    MAX(i.valor) FILTER (WHERE i.nivel_cod='4b' AND i.dimension_cod='pf') AS idps_pf_4b,
    MAX(i.valor) FILTER (WHERE i.nivel_cod='4b' AND i.dimension_cod='hv') AS idps_hv_4b,

    -- Indicadores de ausencia: la no medicion es informacion, no defecto
    (COUNT(s.puntaje) FILTER (WHERE s.nivel_cod='2m') = 0) AS sin_medicion_2m,
    (COUNT(s.puntaje) FILTER (WHERE s.nivel_cod='8b') = 0) AS sin_medicion_8b

FROM hechos.sned_resultado r
JOIN core.periodo p  ON p.periodo_id = r.periodo_id
LEFT JOIN core.establecimiento_periodo ep
       ON ep.rbd = r.rbd AND ep.periodo_id = r.periodo_id
LEFT JOIN hechos.simce_medicion s
       ON s.rbd = r.rbd AND s.periodo_id = r.periodo_id
LEFT JOIN hechos.idps_medicion i
       ON i.rbd = r.rbd AND i.periodo_id = r.periodo_id
GROUP BY r.rbd, r.periodo_id, p.etiqueta, r.cluster_codigo, r.indicer, ep.cod_depe2, ep.es_rural;

-- El indice unico es requisito de REFRESH ... CONCURRENTLY.
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_matriz ON ml.mv_matriz_entrenamiento (rbd, periodo_id);

COMMENT ON MATERIALIZED VIEW ml.mv_matriz_entrenamiento IS
  'Unico objeto materializado. Deshace el formato largo solo para alimentar los algoritmos.';
