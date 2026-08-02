-- ===========================================================================
-- Vista 2 · Atributo derivado `posicion_en_grupo`, NO almacenado
-- ---------------------------------------------------------------------------
-- Aplicacion estricta de la regla 5: un atributo derivado no se guarda, se
-- calcula. Aqui ademas hay una razon de dominio: la posicion cambia cada vez
-- que cambia cualquier establecimiento del grupo, de modo que almacenarla
-- garantizaria valores obsoletos.
--
-- Es la mecanica efectiva de la seleccion del beneficio: no decide el indice
-- absoluto sino la posicion RELATIVA dentro del grupo homogeneo del periodo.
-- La particion incluye el periodo porque el 35,1 % de los establecimientos
-- cambia de agrupacion entre ciclos.
-- ===========================================================================

CREATE OR REPLACE VIEW hechos.v_ranking_intra_cluster AS
SELECT
    r.rbd,
    r.periodo_id,
    p.etiqueta        AS periodo,
    r.cluster_codigo,
    r.indicer,
    RANK() OVER (PARTITION BY r.periodo_id, r.cluster_codigo
                 ORDER BY r.indicer DESC)                      AS posicion_en_grupo,
    COUNT(*) OVER (PARTITION BY r.periodo_id, r.cluster_codigo) AS n_grupo,
    ROUND((PERCENT_RANK() OVER (PARTITION BY r.periodo_id, r.cluster_codigo
                                ORDER BY r.indicer))::numeric, 4) AS percentil,
    r.sel
FROM hechos.sned_resultado r
JOIN core.periodo p ON p.periodo_id = r.periodo_id
WHERE r.indicer IS NOT NULL;

COMMENT ON VIEW hechos.v_ranking_intra_cluster IS
  'Deriva posicion_en_grupo y percentil. Particiona por periodo Y cluster (hallazgo del 35,1 %).';
