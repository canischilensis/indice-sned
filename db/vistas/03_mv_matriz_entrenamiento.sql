-- Matriz ancha de entrenamiento, equivalente a tabla_modelo_largo.parquet.
-- Materializada porque el pivot es costoso y los datos son estáticos
-- (reentrenamiento bianual, no continuo).
--
-- El conjunto depurado NO se reconstruye aquí: se CONSUME desde
-- core.conjunto_entrenamiento, que se puebla con los RBD de
-- tabla_modelo_final_v11.parquet, ya depurado aguas arriba.
CREATE TABLE IF NOT EXISTS core.conjunto_entrenamiento (
    rbd     INTEGER PRIMARY KEY REFERENCES core.establecimiento(rbd),
    origen  TEXT NOT NULL DEFAULT 'tabla_modelo_final_v11.parquet'
);

COMMENT ON TABLE core.conjunto_entrenamiento IS
    'Lista maestra de establecimientos del conjunto depurado. La base guarda los 5 ciclos y los 11.569 RBD; la restriccion a la ventana de entrenamiento vive aqui y en la vista materializada.';

CREATE MATERIALIZED VIEW IF NOT EXISTS ml.mv_matriz_entrenamiento AS
SELECT
    sr.rbd,
    sr.periodo_id,
    p.etiqueta                                   AS ciclo_sned,
    sr.cluster_codigo,
    ep.cod_depe2,
    ep.es_rural,
    sr.indicer,
    sr.sel,
    MAX(CASE WHEN sm.nivel_cod='4b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_4b,
    MAX(CASE WHEN sm.nivel_cod='4b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_4b,
    MAX(CASE WHEN sm.nivel_cod='6b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_6b,
    MAX(CASE WHEN sm.nivel_cod='6b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_6b,
    MAX(CASE WHEN sm.nivel_cod='8b' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_8b,
    MAX(CASE WHEN sm.nivel_cod='8b' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_8b,
    MAX(CASE WHEN sm.nivel_cod='2m' AND sm.asignatura_cod='LECT' THEN sm.puntaje END) AS simce_lect_2m,
    MAX(CASE WHEN sm.nivel_cod='2m' AND sm.asignatura_cod='MATE' THEN sm.puntaje END) AS simce_mate_2m
FROM hechos.sned_resultado sr
JOIN core.conjunto_entrenamiento ce ON ce.rbd = sr.rbd
JOIN core.periodo p  ON p.periodo_id = sr.periodo_id AND p.tipo = 'CICLO_SNED'
LEFT JOIN core.establecimiento_periodo ep
       ON ep.rbd = sr.rbd AND ep.periodo_id = sr.periodo_id
LEFT JOIN core.periodo pm
       ON pm.tipo = 'BIENIO_MEDICION' AND pm.etiqueta = '2018-19'
LEFT JOIN hechos.simce_medicion sm
       ON sm.rbd = sr.rbd AND sm.periodo_id = pm.periodo_id
WHERE p.etiqueta IN ('2020-21', '2022-23', '2024-25')
GROUP BY sr.rbd, sr.periodo_id, p.etiqueta, sr.cluster_codigo, ep.cod_depe2,
         ep.es_rural, sr.indicer, sr.sel;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_matriz ON ml.mv_matriz_entrenamiento(rbd, ciclo_sned);

-- Refrescar tras cada ciclo de ingesta:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY ml.mv_matriz_entrenamiento;
