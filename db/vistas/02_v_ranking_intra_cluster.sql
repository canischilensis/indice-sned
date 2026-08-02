-- Posición del establecimiento dentro de su grupo homogéneo.
-- Es la mecánica real de la selección SNED: se compite dentro del cluster.
CREATE OR REPLACE VIEW hechos.v_ranking_intra_cluster AS
SELECT
    sr.rbd,
    sr.periodo_id,
    sr.cluster_codigo,
    sr.indicer,
    sr.sel,
    RANK()       OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo
                       ORDER BY sr.indicer DESC) AS posicion_en_grupo,
    COUNT(*)     OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo) AS n_grupo,
    PERCENT_RANK() OVER (PARTITION BY sr.periodo_id, sr.cluster_codigo
                         ORDER BY sr.indicer) AS percentil
FROM hechos.sned_resultado sr
WHERE sr.cluster_codigo IS NOT NULL;
