-- =============================================================================
-- VISTAS DE CONSUMO
-- =============================================================================

-- Reconstrucción del INDICER desde los factores, usando las ponderaciones
-- almacenadas en el catálogo. Permite auditar cualquier discrepancia entre
-- el valor oficial y la fórmula declarada.
--
-- n_factores permite restringir la auditoría a los establecimientos con los
-- seis factores presentes. Sin ese filtro la discrepancia refleja factores
-- ausentes, no un error de fórmula.
CREATE OR REPLACE VIEW hechos.v_indicer_reconstruido AS
SELECT
    sf.rbd,
    sf.periodo_id,
    ROUND(SUM(sf.valor * f.ponderacion), 3) AS indicer_calculado,
    sr.indicer                              AS indicer_oficial,
    ROUND(ABS(SUM(sf.valor * f.ponderacion) - sr.indicer), 4) AS discrepancia,
    COUNT(*)                                AS n_factores
FROM hechos.sned_factor sf
JOIN core.factor_sned   f  ON f.factor_cod = sf.factor_cod
JOIN hechos.sned_resultado sr
     ON sr.rbd = sf.rbd AND sr.periodo_id = sf.periodo_id
GROUP BY sf.rbd, sf.periodo_id, sr.indicer;
